-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: car_data
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `car_sales`
--

DROP TABLE IF EXISTS `car_sales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `car_sales` (
  `Brand_name` text,
  `Car_name` text,
  `Price` text,
  `Sales_2023` text,
  `Sales_2024` text,
  `change_rate` text,
  `Total_2023` text,
  `Total_2024` text,
  `Total_Change_rate` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `car_sales`
--

LOCK TABLES `car_sales` WRITE;
/*!40000 ALTER TABLE `car_sales` DISABLE KEYS */;
INSERT INTO `car_sales` VALUES ('포르쉐','911','2억 5,160 만원~','663','1,235','86.30%',' 8,282 ',' 6,617 ','-20.1%'),('BMW','Z4','7,580 만원~','302','621','105.60%',NULL,NULL,NULL),('포르쉐','Taycan','1억 2,990 만원~','1,214','909','-25.10%',NULL,NULL,NULL),('벤츠','SL-Class','1억 5,560 만원~','330','245','-25.80%',NULL,NULL,NULL),('포르쉐','Panamera','1억 7,670 만원~','1,492','1,331','-10.80%',NULL,NULL,NULL),('포드','Mustang','7,870 만원~','680','563','-17.20%',NULL,NULL,NULL),('BMW','M8','2억 4,790 만원~','84','43','-48.80%',NULL,NULL,NULL),('BMW','M5','1억 7,100만원~','464','53','-88.60%',NULL,NULL,NULL),('BMW','M4','1억 3,770 만원~','435','361','-17.00%',NULL,NULL,NULL),('BMW','M3','1억 3,440 만원~','304','305','0.30%',NULL,NULL,NULL),('BMW','M2','7,460 만원~','380','180','-52.60%',NULL,NULL,NULL),('렉서스','LC','1억 8,170 만원~','46','19','-58.70%',NULL,NULL,NULL),('람보르기니','Huracan EVO','3억 2,890 만원~','164','49','-70.10%',NULL,NULL,NULL),('도요타','GR SUPRA','7,980 만원~','218','123','-43.60%',NULL,NULL,NULL),('재규어','F-Type','1억 400만원~','188','0','-100.00%',NULL,NULL,NULL),('밴츠','AMG GT','1억 5,440 만원~','806','142','-82.40%',NULL,NULL,NULL),('포르쉐','718 Boxster','1억 3,530 만원~','141','307','117.70%',NULL,NULL,NULL),('포르쉐','718 Cayman','1억 3,050 만원~','371','131','-64.70%',NULL,NULL,NULL);
/*!40000 ALTER TABLE `car_sales` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-04-10 12:15:32
