-- SHOW TABLE STATUS LIKE 'naver_news'
-- DESCRIBE minute_candlestick;
-- select * from daily_candlestick;
-- SELECT * FROM daily_candlestick WHERE 종목명 IN ('포스코DX');
-- SELECT * FROM daily_candlestick WHERE 종목명 IN ('네오셈');
-- SELECT * FROM daily_candlestick WHERE 종목명 IN ('삼성SDI');
-- SELECT * FROM daily_candlestick WHERE 종목명 IN ('삼성전자') LIMIT 1000;
-- SELECT COUNT(*) FROM daily_candlestick WHERE 종목명 = '삼성전자';





-- SHOW CREATE TABLE daily_candlestick;



-- select * from minute_candlestick;
-- SELECT * FROM minute_candlestick WHERE 종목명 IN ('현대힘스');



--  CREATE TABLE IF NOT EXISTS daily_candlestick (
--             datetime DATE,
--             name VARCHAR(100),
--             Open INT,
--             High INT,
--             Low INT,
--             Close INT,
--             Changes INT,
--             ChangeRate FLOAT,
--             Volume INT,
--             TradingValue FLOAT,
--             Program INT,
--             ForeignNetBuy INT,
--             InstitutionNetBuy INT,
--             IndividualNetBuy INT,
--             PRIMARY KEY (datetime, name) );daily_candlestick


-- CREATE TABLE IF NOT EXISTS naver_news (
--             title VARCHAR(255),
--             originallink VARCHAR(255),
--             link	 VARCHAR(255),
--             description VARCHAR(255),
--             pubDate DATETIME,
--             PRIMARY KEY (originallink)
--         );

-- ALTER TABLE `daily_candlestick`
-- CHANGE COLUMN `datetime` `일자` DATETIME NOT NULL,
-- CHANGE COLUMN `name` `종목명` VARCHAR(100) NOT NULL,
-- CHANGE COLUMN `Open` `시가` INT DEFAULT NULL,
-- CHANGE COLUMN `High` `고가` INT DEFAULT NULL,
-- CHANGE COLUMN `Low` `저가` INT DEFAULT NULL,
-- CHANGE COLUMN `Close` `현재가` INT DEFAULT NULL,
-- CHANGE COLUMN `Volume` `거래량` INT DEFAULT NULL,
-- CHANGE COLUMN `TradingValue` `거래대금` FLOAT DEFAULT NULL,
-- DROP PRIMARY KEY,
-- ADD PRIMARY KEY (`일자`, `종목명`);

-- ALTER TABLE `minute_candlestick`
-- CHANGE COLUMN `종가` `현재가` INT DEFAULT NULL

-- UPDATE daily_candlestick 
-- SET 일자 = DATE(일자);

-- ALTER TABLE daily_candlestick 
-- MODIFY COLUMN 거래대금 INT;

-- DELETE FROM daily_candlestick 
-- WHERE 일자 = '0000-00-00';


-- SET SQL_SAFE_UPDATES = 0;
-- DELETE FROM daily_candlestick WHERE 종목명 = '삼성전자' LIMIT 100;
-- SET SQL_SAFE_UPDATES = 1;

-- ALTER TABLE daily_candlestick
-- DROP COLUMN `Changes`,
-- DROP COLUMN `ChangeRate`,
-- DROP COLUMN `Program`,
-- DROP COLUMN `ForeignNetBuy`,
-- DROP COLUMN `InstitutionNetBuy`,
-- DROP COLUMN `IndividualNetBuy`;