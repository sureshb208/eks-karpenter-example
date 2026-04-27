Build a Terraform setup to create AWS Glue Catalog resources in region us-west-2.

Requirements:
	•	Create one Glue database named “demo_glue_db”
	•	Create one external Glue table named “sales_data”
	•	Table should point to an S3 location (use a variable for bucket name)
	•	Use Parquet format
	•	Add sample columns: order_id (string), order_date (date), revenue (double)
	•	Do NOT include Glue jobs, crawlers, or connections
	•	Do NOT include KMS configuration
	•	Keep it minimal and production-ready

Structure:
	•	provider.tf (set region to us-west-2)
	•	variables.tf (for bucket name)
	•	main.tf (database and table resources)

Additional:
	•	Ensure code is reusable and clean
	•	No hardcoding except database/table names
	•	Add comments where needed

Output:
	•	Complete Terraform code in separate files (provider.tf, variables.tf, main.tf)