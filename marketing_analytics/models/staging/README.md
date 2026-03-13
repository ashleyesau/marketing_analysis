# Staging Layer

Five dbt models that clean, type-cast, and deduplicate raw seed data before it enters the transformation pipeline.

---

## Role in the Wider Project

- First transformation layer in the marketing_analysis dbt pipeline
- Each model reads directly from one raw seed table loaded by `dbt seed`; no staging model reads from another staging model or from intermediate models
- All five intermediate models source exclusively from staging views; no downstream model reads raw seed tables directly
- Handles all concerns that belong at the source boundary: data type casting, string normalisation, null coalescing, and deduplication
- Materialised as views so that no data is duplicated at this layer; intermediate and mart models materialise the results

---

## What It Contains

- `stg_customers.sql` - Cleans and type-casts the customers seed; lowercases and trims country, gender, loyalty_tier, and acquisition_channel; coalesces null loyalty_tier and acquisition_channel to 'unknown'; 100,000 rows
- `stg_campaigns.sql` - Cleans and type-casts the campaigns seed; lowercases channel, objective, and target_segment; casts start_date, end_date, and expected_uplift; 50 rows
- `stg_products.sql` - Cleans, type-casts, and deduplicates the products seed using row_number() partitioned by product_id ordered by launch_date; lowercases category and brand; 2,000 rows
- `stg_events.sql` - Cleans, type-casts, and deduplicates the events seed; renames timestamp to event_timestamp; lowercases event_type, device_type, traffic_source, page_category, and experiment_group; filters null session_ids; 2,000,000 rows
- `stg_transactions.sql` - Cleans, type-casts, and deduplicates the transactions seed; renames timestamp to transaction_timestamp; derives is_refunded boolean from the integer refund_flag column; 103,127 rows
- `schema.yml` - Column-level documentation and dbt tests (not_null, unique, accepted_values) for all five models

---

## Inputs and Outputs

Inputs:

- `dev.customers` - raw customers seed table
- `dev.campaigns` - raw campaigns seed table
- `dev.products` - raw products seed table
- `dev.events` - raw events seed table
- `dev.transactions` - raw transactions seed table

Outputs (all materialised as views in the dev schema):

- `dev.stg_customers`
- `dev.stg_campaigns`
- `dev.stg_products`
- `dev.stg_events`
- `dev.stg_transactions`

---

## Notes

- The `acquisition_channel` column in stg_customers is the customer-level channel at signup. It is intentionally not renamed to `traffic_source`. Both stg_customers and stg_events contain a channel-related field, but they represent different concepts: acquisition_channel is set once at signup; traffic_source in stg_events is a session-level attribute recorded per event. Conflating them would be a silent semantic error.
- The `base_price` column in stg_products is the product price field. There is no `price` column in the source data.
- The `discount_applied` column in stg_transactions is the discount field. There is no `discount_amount` column in the source data.
- There is no `product_name` column in the products source data. Products are identified by product_id, category, and brand only.
- There is no `campaign_name` column in the campaigns source data.
- stg_events contains an `experiment_group` field (values: control, variant_a, variant_b) that surfaces in the mart layer as fct_experiment_groups.
