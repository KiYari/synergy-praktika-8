-- Основная таблица проблем/инцидентов
CREATE TABLE problems (
    issue_id VARCHAR(50) PRIMARY KEY,
    user_description TEXT NOT NULL,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'new'
);

-- Таблица симптомов
CREATE TABLE symptoms (
    symptom_id SERIAL PRIMARY KEY,
    issue_id VARCHAR(50) NOT NULL REFERENCES problems(issue_id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    environment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица предпринятых действий
CREATE TABLE actions (
    action_id SERIAL PRIMARY KEY,
    issue_id VARCHAR(50) NOT NULL REFERENCES problems(issue_id) ON DELETE CASCADE,
    action_taken VARCHAR(50) NOT NULL,
    result VARCHAR(20) NOT NULL,
    performed_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица решений
CREATE TABLE solutions (
    solution_id VARCHAR(50) PRIMARY KEY,
    issue_id VARCHAR(50) NOT NULL REFERENCES problems(issue_id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    steps TEXT NOT NULL,
    confidence FLOAT,
    for_line VARCHAR(20) NOT NULL,
    is_applied BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP,
    result VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица возможных причин (выводы системы)
CREATE TABLE possible_causes (
    cause_id SERIAL PRIMARY KEY,
    issue_id VARCHAR(50) NOT NULL REFERENCES problems(issue_id) ON DELETE CASCADE,
    cause_description TEXT NOT NULL,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица знаний (правила)
CREATE TABLE knowledge_rules (
    rule_id SERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    condition_symptoms JSONB,
    recommended_solution TEXT,
    solution_steps TEXT,
    target_line VARCHAR(20),
    confidence_weight FLOAT DEFAULT 1.0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);