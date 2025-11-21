# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "11d5a2f9-aac4-4120-8c3d-71415bcc85d5",
# META       "default_lakehouse_name": "SilverLakehouse",
# META       "default_lakehouse_workspace_id": "dfeef225-5614-4404-b47a-3fbaecefac22",
# META       "known_lakehouses": [
# META         {
# META           "id": "11d5a2f9-aac4-4120-8c3d-71415bcc85d5"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from datetime import date
import random
from pyspark.sql import SparkSession
from pyspark.sql import Row

# Create sample Customers data
customers = [
    Row(customer_id=i, 
        name=f'Customer_{i}', 
        email=f'customer{i}@example.com',
        signup_date=date(2023, 1, 1).replace(day=random.randint(1,28), month=random.randint(1,12)),
        country=random.choice(['USA', 'Canada', 'UK', 'Germany', 'France'])
    ) for i in range(1, 11)
]

# Create sample Orders data
orders = []
for i in range(1, 21):
    cust_id = random.randint(1, 10)
    orders.append(
        Row(order_id=i,
            customer_id=cust_id,
            order_date=date(2024, random.randint(1,12), random.randint(1,28)),
            amount=round(random.uniform(10.0, 200.0), 2),
            status=random.choice(['Pending', 'Shipped', 'Delivered', 'Cancelled'])
        )
    )

spark = SparkSession.builder.getOrCreate()
df_customers = spark.createDataFrame(customers)
df_orders = spark.createDataFrame(orders)

# Save sample customers as Delta table
df_customers.write.format("delta").mode("overwrite").saveAsTable("Customers")

# Save sample orders as Delta table
df_orders.write.format("delta").mode("overwrite").saveAsTable("Orders")

print("Tables saved as Delta tables in the Lakehouse")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import com.microsoft.spark.fabric
from com.microsoft.spark.fabric.Constants import Constants

df_customers.write.mode("overwrite").synapsesql("GoldWarehouse.dbo.Customers")
df_orders.write.mode("overwrite").synapsesql("GoldWarehouse.dbo.Orders")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
