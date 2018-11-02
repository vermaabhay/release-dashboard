CREATE DATABASE ReleaseDashboard;

use ReleaseDashboard;

CREATE TABLE ReleaseData(
	ID INT NOT NULL AUTO_INCREMENT,
	ReleaseDate DATETIME DEFAULT CURRENT_TIMESTAMP,
	CompName VARCHAR(100) NOT NULL,
	SubCompName VARCHAR(100) NOT NULL,
	SprintLink VARCHAR(10000) DEFAULT NULL,
	ConfluenceLink VARCHAR(10000) DEFAULT NULL,
	ProdPromoter VARCHAR(100) NOT NULL,
	ReleaseBranch VARCHAR(100) NOT NULL,
	BuildNum INT NOT NULL,
	PRIMARY KEY(ID));

CREATE USER jenkins;

GRANT SELECT,INSERT,UPDATE ON ReleaseDashboard.* TO jenkins@'10.65.%' IDENTIFIED BY '';
GRANT SELECT,INSERT,UPDATE ON ReleaseDashboard.* TO jenkins@'10.70.%' IDENTIFIED BY '';


CREATE USER dash;

GRANT SELECT ON ReleaseDashboard.* TO dash@'10.65.%' IDENTIFIED BY '';
GRANT SELECT ON ReleaseDashboard.* TO dash@'10.70.%' IDENTIFIED BY '';


FLUSH PRIVILEGES;
