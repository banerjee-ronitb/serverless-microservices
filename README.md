# Serverless Microservices
A reference implementation with Monorepo based choreography saga design  pattern with lambda functions and dynamo db.

## Services

| Service Name                                                                        | Responsibility                               |
|-------------------------------------------------------------------------------------|----------------------------------------------|
| [Create Order Service](services%2Forder-service%2Fcreate-order)                     | Creates an order in Order Table              |
| [Confirm Order Service](services%2Forder-service%2Fconfirm-order)                   | Confirms the order in order Table            |
| [Cancel Order Service](services%2Forder-service%2Fcancel-order)                     | Cancels an order in order Table              |
| [Retrieve Catalog Service](services%2Fcatalog-service%2Fretrieve-catalog)           | List the catalog with pagination             |
| [Update Catalog Service](services%2Fcatalog-service%2Fupdate-catalog)               | Updates the catalog/inventory                |
| [Create Payment Intent Service](services%2Fpayment-service%2Fcreate-payment-intent) | Creates a payment intent in stripe           |
| [Payment Intent Webhook](services%2Fpayment-service%2Fpayment-intent-webhook)       | Webhook to receive payment events from Strip |
| [Refund Payment Service](services%2Fpayment-service%2Frefund-payment)               | Service to refund a payment                  |
## Flow Diagram

![Flow Diagram.png](shared%2Fassets%2FFlow%20Diagram.png)

## Tech Stacks Used

![TechStacksUsed.png](shared%2Fassets%2FTechStacksUsed.png)

## Architecture Diagram


![architecture diagram.png](shared%2Fassets%2Farchitecture%20diagram.png)
