DROP TABLE IF EXISTS urls;
DROP TABLE IF EXISTS url_checks;

CREATE TABLE urls (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE url_checks (
  id SERIAL PRIMARY KEY,
  url_id SERIAL REFERENCES urls (id),
  status_code SMALLINT,
  h1 TEXT,
  title TEXT,
  description TEXT,
  created_at TIMESTAMP NOT NULL
);
