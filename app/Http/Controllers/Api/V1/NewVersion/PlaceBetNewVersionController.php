<?php

namespace App\Http\Controllers\Api\V1\NewVersion;

use App\Enums\SlotWebhookResponseCode;
use App\Enums\TransactionName;
use App\Http\Controllers\Api\V1\Webhook\Traits\NewVersionOptimizedBettingProcess;
use App\Http\Controllers\Controller;
use App\Http\Requests\Slot\SlotWebhookRequest;
use App\Models\User;
use App\Services\Slot\SlotWebhookService;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Redis;
use Illuminate\Support\Facades\Http;

class PlaceBetNewVersionController extends Controller
{
    use NewVersionOptimizedBettingProcess;

    public function placeBetNew(SlotWebhookRequest $request)
    {
        $userId = $request->getMember()->id;

        // Retry logic for acquiring the Redis lock
        $attempts = 0;
        $maxAttempts = 3;
        $lock = false;

        while ($attempts < $maxAttempts && ! $lock) {
            $lock = Redis::set("wallet:lock:$userId", true, 'EX', 15, 'NX'); // 15 seconds lock
            $attempts++;

            if (! $lock) {
                sleep(1); // Wait for 1 second before retrying
            }
        }

        if (! $lock) {
            return response()->json([
                'message' => 'Another transaction is currently processing. Please try again later.',
                'userId' => $userId
            ], 409); // 409 Conflict
        }

        // Validate the structure of the request
        $validator = $request->check();

        if ($validator->fails()) {
            Redis::del("wallet:lock:$userId");
            return $validator->getResponse();
        }

        // Step 1: Gather transaction data from the request
        $transactionData = $request->all();

        // Step 2: Send the data to the Python fraud detection service
        $response = Http::post('https://www.allinonetestcase.online/predict_fraud', [
            'Transactions' => $transactionData['Transactions'],  // Sending transactions to Flask for fraud check
        ]);

        // Step 3: Check if the response is valid and contains the 'fraudulent' key
        if ($response->failed()) {
            Log::error('Fraud detection service failed.', ['response' => $response->body()]);
            Redis::del("wallet:lock:$userId");
            return response()->json(['message' => 'Fraud detection service failed.'], 500);
        }

        $responseData = $response->json();
        if (!isset($responseData['fraudulent'])) {
            Log::error('Fraud detection service returned an invalid response', ['response' => $responseData]);
            Redis::del("wallet:lock:$userId");
            return response()->json([
                'message' => 'Invalid response from fraud detection service.',
                'details' => $responseData
            ], 500);
        }

        // Step 4: Get the fraud prediction result safely
        $isFraudulent = $responseData['fraudulent'];

        // Step 5: Continue processing the bet if no fraud detected
        $before_balance = $request->getMember()->balanceFloat;

        // Retrieve transactions from the request
        $transactions = $validator->getRequestTransactions();

        if (!is_array($transactions) || empty($transactions)) {
            Redis::del("wallet:lock:$userId");
            return response()->json([
                'message' => 'Invalid transaction data format.',
                'details' => $transactions,  // Provide details about the received data for debugging
            ], 400);  // 400 Bad Request
        }

        DB::beginTransaction();
        try {
            // Create and store the event in the database
            $event = $this->createEvent($request);

            // Insert bets using chunking for better performance
            $message = $this->insertBets($transactions, $event);  // Insert bets in chunks

            DB::commit();  // Commit only the bet insertion

        } catch (\Exception $e) {
            DB::rollBack();
            Log::error('Error during placeBet', ['error' => $e]);
            Redis::del("wallet:lock:$userId");
            return response()->json(['message' => $e->getMessage()], 500);
        }

        // After the transaction, handle the wallet updates separately
        try {
            foreach ($transactions as $transaction) {
                if (!isset($transaction->WagerID) || !isset($transaction->TransactionID)) {
                    return response()->json(['message' => 'Invalid transaction data structure.'], 400);
                }

                $meta = [
                    'wager_id' => $transaction->WagerID,
                    'event_id' => $request->getMessageID(),
                    'seamless_transaction_id' => $transaction->TransactionID,
                ];

                $this->processTransfer(
                    $request->getMember(),
                    User::adminUser(),
                    TransactionName::Stake,
                    $transaction->TransactionAmount,
                    $transaction->Rate,
                    $meta
                );
            }

            // Refresh balance after transactions
            $request->getMember()->wallet->refreshBalance();
            $after_balance = $request->getMember()->balanceFloat;

        } catch (\Exception $e) {
            Log::error('Error during wallet transfer processing', ['error' => $e]);
            Redis::del("wallet:lock:$userId");
            return response()->json(['message' => $e->getMessage()], 500);
        }

        // Release the Redis lock
        Redis::del("wallet:lock:$userId");

        return SlotWebhookService::buildResponse(
            SlotWebhookResponseCode::Success,
            $after_balance,
            $before_balance
        );
    }
}