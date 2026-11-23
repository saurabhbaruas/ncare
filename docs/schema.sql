-- Generated from the SQLAlchemy models (PostgreSQL). Tables are also created automatically on first start.

CREATE TABLE locations (
	id SERIAL NOT NULL, 
	code VARCHAR(10) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
)

;

CREATE TABLE permissions (
	id SERIAL NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
)

;

CREATE TABLE roles (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	parent_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(parent_id) REFERENCES roles (id)
)

;

CREATE TABLE teams (
	id SERIAL NOT NULL, 
	code VARCHAR(10) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
)

;

CREATE TABLE role_permissions (
	role_id INTEGER NOT NULL, 
	permission_id INTEGER NOT NULL, 
	PRIMARY KEY (role_id, permission_id), 
	FOREIGN KEY(role_id) REFERENCES roles (id), 
	FOREIGN KEY(permission_id) REFERENCES permissions (id)
)

;

CREATE TABLE users (
	id SERIAL NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	full_name VARCHAR(100) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role_id INTEGER NOT NULL, 
	location_id INTEGER NOT NULL, 
	team_id INTEGER NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	failed_attempts INTEGER NOT NULL, 
	locked_until TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id), 
	FOREIGN KEY(location_id) REFERENCES locations (id), 
	FOREIGN KEY(team_id) REFERENCES teams (id)
)

;

CREATE TABLE auth_logs (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	email VARCHAR(255) NOT NULL, 
	success BOOLEAN NOT NULL, 
	reason VARCHAR(100) NOT NULL, 
	ip_address VARCHAR(64), 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE data_audit (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	action VARCHAR(30) NOT NULL, 
	patient_id VARCHAR(30), 
	detail TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;

CREATE TABLE patients (
	id SERIAL NOT NULL, 
	patient_id VARCHAR(30) NOT NULL, 
	manager_id INTEGER NOT NULL, 
	first_name BYTEA NOT NULL, 
	last_name BYTEA NOT NULL, 
	dob BYTEA NOT NULL, 
	gender BYTEA NOT NULL, 
	key_version INTEGER NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_manager_patient UNIQUE (manager_id, patient_id), 
	FOREIGN KEY(manager_id) REFERENCES users (id)
)

;

CREATE TABLE reset_tokens (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	used BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	UNIQUE (token_hash)
)

;
