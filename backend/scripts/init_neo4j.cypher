CREATE CONSTRAINT account_number_unique IF NOT EXISTS
FOR (a:Account) REQUIRE a.accountNumber IS UNIQUE;

CREATE CONSTRAINT transaction_ref_unique IF NOT EXISTS
FOR (t:Transaction) REQUIRE t.transactionRef IS UNIQUE;

CREATE INDEX account_label_risk IF NOT EXISTS
FOR (a:Account) ON (a.label, a.riskScore);

CREATE INDEX account_bank IF NOT EXISTS
FOR (a:Account) ON (a.bankName);

CREATE FULLTEXT INDEX account_name_search IF NOT EXISTS
FOR (a:Account) ON EACH [a.registeredName, a.accountNumber];
