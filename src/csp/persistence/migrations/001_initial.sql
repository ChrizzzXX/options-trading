-- Slice 6 initial schema: ideas + trades + migration tracker.
-- Money fields: DECIMAL(18,4); ratios: DOUBLE; dates: DATE; timestamps: TIMESTAMP UTC.

CREATE TABLE ideas (
    idea_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    as_of DATE NOT NULL,
    pflichtregeln_passed BOOLEAN NOT NULL,
    bypassed_count INTEGER NOT NULL DEFAULT 0,
    region TEXT NOT NULL,
    data_freshness TEXT NOT NULL,
    annualized_yield_pct DOUBLE NOT NULL,
    idea_json JSON NOT NULL,
    inserted_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_ideas_ticker_as_of ON ideas (ticker, as_of);
CREATE INDEX idx_ideas_bypassed_count ON ideas (bypassed_count);

CREATE TABLE trades (
    trade_id TEXT PRIMARY KEY,
    idea_id TEXT NOT NULL REFERENCES ideas(idea_id),
    ticker TEXT NOT NULL,
    status TEXT NOT NULL,
    contracts INTEGER NOT NULL,
    open_date DATE NOT NULL,
    open_premium DECIMAL(18,4) NOT NULL,
    cash_secured DECIMAL(18,4) NOT NULL,
    close_date DATE,
    close_premium DECIMAL(18,4),
    pnl DECIMAL(18,4),
    notes TEXT,
    inserted_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_trades_status ON trades (status);
CREATE INDEX idx_trades_idea ON trades (idea_id);
