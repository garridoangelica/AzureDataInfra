CREATE TABLE [dbo].[Orders] (

	[order_id] bigint NULL, 
	[customer_id] bigint NULL, 
	[order_date] date NULL, 
	[amount] float NULL, 
	[status] varchar(max) NULL
);