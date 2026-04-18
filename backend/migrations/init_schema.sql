CREATE TABLE IF NOT EXISTS merchants (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  business_type VARCHAR(100),
  owner_name VARCHAR(255),
  kyc_status VARCHAR(50) DEFAULT 'VERIFIED',
  industry VARCHAR(100),
  years_in_business INT DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transaction_logs (
  id SERIAL PRIMARY KEY,
  merchant_id VARCHAR(50) REFERENCES merchants(id) ON DELETE CASCADE,
  customer_id VARCHAR(50) NOT NULL,
  amount DECIMAL(15, 2) NOT NULL,
  is_refund BOOLEAN DEFAULT FALSE,
  pos_terminal_id VARCHAR(100),
  transaction_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_requests (
  id VARCHAR(100) PRIMARY KEY,
  merchant_id VARCHAR(50) REFERENCES merchants(id) ON DELETE CASCADE,
  customer_id VARCHAR(50) NOT NULL,
  loan_type TEXT NOT NULL,
  requested_amount DECIMAL(15, 2) NOT NULL,
  ai_score INT,
  risk_label VARCHAR(50),
  pd_value DECIMAL(10, 4),
  default_probability DECIMAL(10, 4),
  label_quantile VARCHAR(50),
  label_cic_range VARCHAR(50),
  ai_agent_report TEXT,
  status VARCHAR(50) DEFAULT 'PENDING',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
  user_id VARCHAR(50) PRIMARY KEY,
  username VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) DEFAULT 'BANKER',
  merchant_id VARCHAR(50) REFERENCES merchants(id) ON DELETE SET NULL,
  customer_id VARCHAR(50) DEFAULT NULL,
  status VARCHAR(20) DEFAULT 'ACTIVE',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (user_id, username, password_hash, role)
VALUES ('usr_admin_001', 'admin', 'admin', 'ADMIN')
ON CONFLICT (username) DO NOTHING;

CREATE INDEX IF NOT EXISTS idx_transactions_merchant_id ON transaction_logs(merchant_id);
CREATE INDEX IF NOT EXISTS idx_transactions_history ON transaction_logs(merchant_id, customer_id, transaction_time);
CREATE INDEX IF NOT EXISTS idx_loans_merchant_id ON loan_requests(merchant_id);
CREATE INDEX IF NOT EXISTS idx_loans_customer_id ON loan_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
