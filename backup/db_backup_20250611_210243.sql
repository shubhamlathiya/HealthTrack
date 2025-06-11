-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: healthtrack_demo
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `additional_charge`
--

DROP TABLE IF EXISTS `additional_charge`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `additional_charge` (
  `id` int NOT NULL AUTO_INCREMENT,
  `call_id` int DEFAULT NULL,
  `charge_item_id` int DEFAULT NULL,
  `amount` float NOT NULL,
  `notes` text,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `call_id` (`call_id`),
  KEY `charge_item_id` (`charge_item_id`),
  CONSTRAINT `additional_charge_ibfk_1` FOREIGN KEY (`call_id`) REFERENCES `ambulance_call` (`id`),
  CONSTRAINT `additional_charge_ibfk_2` FOREIGN KEY (`charge_item_id`) REFERENCES `ambulance_charge_item` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `additional_charge`
--

LOCK TABLES `additional_charge` WRITE;
/*!40000 ALTER TABLE `additional_charge` DISABLE KEYS */;
/*!40000 ALTER TABLE `additional_charge` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ambulance`
--

DROP TABLE IF EXISTS `ambulance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ambulance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vehicle_number` varchar(20) NOT NULL,
  `vehicle_name` varchar(100) NOT NULL,
  `year_made` int NOT NULL,
  `vehicle_type` varchar(50) NOT NULL,
  `base_rate` float NOT NULL,
  `registration_number` varchar(50) DEFAULT NULL,
  `insurance_number` varchar(50) DEFAULT NULL,
  `insurance_expiry` date DEFAULT NULL,
  `facilities` text,
  `is_available` tinyint(1) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `driver_id` int DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `vehicle_number` (`vehicle_number`),
  KEY `driver_id` (`driver_id`),
  CONSTRAINT `ambulance_ibfk_1` FOREIGN KEY (`driver_id`) REFERENCES `driver` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ambulance`
--

LOCK TABLES `ambulance` WRITE;
/*!40000 ALTER TABLE `ambulance` DISABLE KEYS */;
/*!40000 ALTER TABLE `ambulance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ambulance_call`
--

DROP TABLE IF EXISTS `ambulance_call`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ambulance_call` (
  `id` int NOT NULL AUTO_INCREMENT,
  `call_number` varchar(20) NOT NULL,
  `patient_name` varchar(100) NOT NULL,
  `patient_age` int NOT NULL,
  `patient_gender` varchar(10) NOT NULL,
  `pickup_location` varchar(255) NOT NULL,
  `destination` varchar(255) DEFAULT NULL,
  `call_time` datetime NOT NULL DEFAULT (now()),
  `dispatch_time` datetime DEFAULT NULL,
  `arrival_time` datetime DEFAULT NULL,
  `completion_time` datetime DEFAULT NULL,
  `distance` float DEFAULT NULL,
  `base_charge` float DEFAULT NULL,
  `additional_charges_total` float DEFAULT NULL,
  `subtotal` float DEFAULT NULL,
  `discount_percent` float DEFAULT NULL,
  `discount_amount` float DEFAULT NULL,
  `tax_percent` float DEFAULT NULL,
  `tax_amount` float DEFAULT NULL,
  `total_amount` float DEFAULT NULL,
  `payment_mode` varchar(50) DEFAULT NULL,
  `payment_amount` float DEFAULT NULL,
  `notes` text,
  `status` varchar(20) DEFAULT NULL,
  `ambulance_id` int DEFAULT NULL,
  `driver_id` int DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `call_number` (`call_number`),
  KEY `ambulance_id` (`ambulance_id`),
  KEY `driver_id` (`driver_id`),
  CONSTRAINT `ambulance_call_ibfk_1` FOREIGN KEY (`ambulance_id`) REFERENCES `ambulance` (`id`),
  CONSTRAINT `ambulance_call_ibfk_2` FOREIGN KEY (`driver_id`) REFERENCES `driver` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ambulance_call`
--

LOCK TABLES `ambulance_call` WRITE;
/*!40000 ALTER TABLE `ambulance_call` DISABLE KEYS */;
/*!40000 ALTER TABLE `ambulance_call` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ambulance_category`
--

DROP TABLE IF EXISTS `ambulance_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ambulance_category` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ambulance_category`
--

LOCK TABLES `ambulance_category` WRITE;
/*!40000 ALTER TABLE `ambulance_category` DISABLE KEYS */;
/*!40000 ALTER TABLE `ambulance_category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ambulance_charge_item`
--

DROP TABLE IF EXISTS `ambulance_charge_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ambulance_charge_item` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `standard_charge` float NOT NULL,
  `category_id` int DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `ambulance_charge_item_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `ambulance_category` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ambulance_charge_item`
--

LOCK TABLES `ambulance_charge_item` WRITE;
/*!40000 ALTER TABLE `ambulance_charge_item` DISABLE KEYS */;
/*!40000 ALTER TABLE `ambulance_charge_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `appointment_treatments`
--

DROP TABLE IF EXISTS `appointment_treatments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `appointment_treatments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `appointment_id` int NOT NULL,
  `treatment_id` int NOT NULL,
  `price` float NOT NULL,
  `notes` text,
  `status` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `appointment_id` (`appointment_id`),
  KEY `treatment_id` (`treatment_id`),
  CONSTRAINT `appointment_treatments_ibfk_1` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`id`),
  CONSTRAINT `appointment_treatments_ibfk_2` FOREIGN KEY (`treatment_id`) REFERENCES `treatments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `appointment_treatments`
--

LOCK TABLES `appointment_treatments` WRITE;
/*!40000 ALTER TABLE `appointment_treatments` DISABLE KEYS */;
/*!40000 ALTER TABLE `appointment_treatments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `appointments`
--

DROP TABLE IF EXISTS `appointments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `appointments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `start_time` time NOT NULL,
  `end_time` time NOT NULL,
  `status` varchar(20) DEFAULT NULL,
  `reason` text,
  `notes` text,
  `patient_id` int NOT NULL,
  `doctor_id` int NOT NULL,
  `original_doctor_id` int DEFAULT NULL,
  `original_appointment_id` int DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `canceled_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `patient_id` (`patient_id`),
  KEY `doctor_id` (`doctor_id`),
  KEY `original_doctor_id` (`original_doctor_id`),
  KEY `original_appointment_id` (`original_appointment_id`),
  CONSTRAINT `appointments_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`),
  CONSTRAINT `appointments_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`),
  CONSTRAINT `appointments_ibfk_3` FOREIGN KEY (`original_doctor_id`) REFERENCES `doctor` (`id`),
  CONSTRAINT `appointments_ibfk_4` FOREIGN KEY (`original_appointment_id`) REFERENCES `appointments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `appointments`
--

LOCK TABLES `appointments` WRITE;
/*!40000 ALTER TABLE `appointments` DISABLE KEYS */;
/*!40000 ALTER TABLE `appointments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `availability`
--

DROP TABLE IF EXISTS `availability`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `availability` (
  `id` int NOT NULL AUTO_INCREMENT,
  `day_of_week` varchar(10) NOT NULL,
  `from_time` varchar(20) DEFAULT NULL,
  `to_time` varchar(20) DEFAULT NULL,
  `doctor_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `doctor_id` (`doctor_id`),
  CONSTRAINT `availability_ibfk_1` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `availability`
--

LOCK TABLES `availability` WRITE;
/*!40000 ALTER TABLE `availability` DISABLE KEYS */;
/*!40000 ALTER TABLE `availability` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bed`
--

DROP TABLE IF EXISTS `bed`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bed` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bed_number` int NOT NULL,
  `room_id` int DEFAULT NULL,
  `is_empty` tinyint(1) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `room_id` (`room_id`),
  CONSTRAINT `bed_ibfk_1` FOREIGN KEY (`room_id`) REFERENCES `room` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bed`
--

LOCK TABLES `bed` WRITE;
/*!40000 ALTER TABLE `bed` DISABLE KEYS */;
/*!40000 ALTER TABLE `bed` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bed_allocation`
--

DROP TABLE IF EXISTS `bed_allocation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bed_allocation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bed_id` int NOT NULL,
  `patient_id` int NOT NULL,
  `admission_date` datetime NOT NULL,
  `discharge_date` datetime DEFAULT NULL,
  `expected_discharge` datetime DEFAULT NULL,
  `cleaned_at` datetime DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `bed_id` (`bed_id`),
  KEY `patient_id` (`patient_id`),
  CONSTRAINT `bed_allocation_ibfk_1` FOREIGN KEY (`bed_id`) REFERENCES `bed` (`id`),
  CONSTRAINT `bed_allocation_ibfk_2` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bed_allocation`
--

LOCK TABLES `bed_allocation` WRITE;
/*!40000 ALTER TABLE `bed_allocation` DISABLE KEYS */;
/*!40000 ALTER TABLE `bed_allocation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bed_cleaning_log`
--

DROP TABLE IF EXISTS `bed_cleaning_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bed_cleaning_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bed_id` int NOT NULL,
  `allocation_id` int DEFAULT NULL,
  `cleaned_at` datetime DEFAULT NULL,
  `cleaned_by` int DEFAULT NULL,
  `remarks` text,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `bed_id` (`bed_id`),
  KEY `allocation_id` (`allocation_id`),
  KEY `cleaned_by` (`cleaned_by`),
  CONSTRAINT `bed_cleaning_log_ibfk_1` FOREIGN KEY (`bed_id`) REFERENCES `bed` (`id`),
  CONSTRAINT `bed_cleaning_log_ibfk_2` FOREIGN KEY (`allocation_id`) REFERENCES `bed_allocation` (`id`),
  CONSTRAINT `bed_cleaning_log_ibfk_3` FOREIGN KEY (`cleaned_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bed_cleaning_log`
--

LOCK TABLES `bed_cleaning_log` WRITE;
/*!40000 ALTER TABLE `bed_cleaning_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `bed_cleaning_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blood_donors`
--

DROP TABLE IF EXISTS `blood_donors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blood_donors` (
  `id` int NOT NULL AUTO_INCREMENT,
  `patient_id` int NOT NULL,
  `donation_date` datetime NOT NULL,
  `blood_type` enum('A_POSITIVE','A_NEGATIVE','B_POSITIVE','B_NEGATIVE','AB_POSITIVE','AB_NEGATIVE','O_POSITIVE','O_NEGATIVE') NOT NULL,
  `units_donated` float NOT NULL,
  `notes` text,
  `status` varchar(20) DEFAULT NULL,
  `last_donation` date DEFAULT NULL,
  `next_eligible` date DEFAULT NULL,
  `emergency_contact_name` varchar(100) DEFAULT NULL,
  `emergency_contact_phone` varchar(20) DEFAULT NULL,
  `emergency_contact_relation` varchar(50) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `patient_id` (`patient_id`),
  CONSTRAINT `blood_donors_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blood_donors`
--

LOCK TABLES `blood_donors` WRITE;
/*!40000 ALTER TABLE `blood_donors` DISABLE KEYS */;
/*!40000 ALTER TABLE `blood_donors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blood_inventory`
--

DROP TABLE IF EXISTS `blood_inventory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blood_inventory` (
  `id` int NOT NULL AUTO_INCREMENT,
  `blood_type` enum('A_POSITIVE','A_NEGATIVE','B_POSITIVE','B_NEGATIVE','AB_POSITIVE','AB_NEGATIVE','O_POSITIVE','O_NEGATIVE') NOT NULL,
  `units_available` float NOT NULL,
  `donation_id` int DEFAULT NULL,
  `expiration_date` datetime NOT NULL,
  `storage_location` varchar(50) DEFAULT NULL,
  `date_added` datetime DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `donation_id` (`donation_id`),
  CONSTRAINT `blood_inventory_ibfk_1` FOREIGN KEY (`donation_id`) REFERENCES `blood_donors` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blood_inventory`
--

LOCK TABLES `blood_inventory` WRITE;
/*!40000 ALTER TABLE `blood_inventory` DISABLE KEYS */;
/*!40000 ALTER TABLE `blood_inventory` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blood_request_items`
--

DROP TABLE IF EXISTS `blood_request_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blood_request_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `request_id` int NOT NULL,
  `blood_type` enum('A_POSITIVE','A_NEGATIVE','B_POSITIVE','B_NEGATIVE','AB_POSITIVE','AB_NEGATIVE','O_POSITIVE','O_NEGATIVE') NOT NULL,
  `units_requested` float NOT NULL,
  `units_approved` float NOT NULL,
  `inventory_id` int DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `request_id` (`request_id`),
  KEY `inventory_id` (`inventory_id`),
  CONSTRAINT `blood_request_items_ibfk_1` FOREIGN KEY (`request_id`) REFERENCES `blood_requests` (`id`),
  CONSTRAINT `blood_request_items_ibfk_2` FOREIGN KEY (`inventory_id`) REFERENCES `blood_inventory` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blood_request_items`
--

LOCK TABLES `blood_request_items` WRITE;
/*!40000 ALTER TABLE `blood_request_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `blood_request_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blood_requests`
--

DROP TABLE IF EXISTS `blood_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blood_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `request_date` datetime NOT NULL,
  `requester_id` int DEFAULT NULL,
  `patient_id` int DEFAULT NULL,
  `department` varchar(50) NOT NULL,
  `status` varchar(20) NOT NULL,
  `priority` varchar(20) NOT NULL,
  `notes` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `requester_id` (`requester_id`),
  KEY `patient_id` (`patient_id`),
  CONSTRAINT `blood_requests_ibfk_1` FOREIGN KEY (`requester_id`) REFERENCES `users` (`id`),
  CONSTRAINT `blood_requests_ibfk_2` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blood_requests`
--

LOCK TABLES `blood_requests` WRITE;
/*!40000 ALTER TABLE `blood_requests` DISABLE KEYS */;
/*!40000 ALTER TABLE `blood_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blood_transfusion_items`
--

DROP TABLE IF EXISTS `blood_transfusion_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blood_transfusion_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transfusion_id` int NOT NULL,
  `blood_type` enum('A_POSITIVE','A_NEGATIVE','B_POSITIVE','B_NEGATIVE','AB_POSITIVE','AB_NEGATIVE','O_POSITIVE','O_NEGATIVE') NOT NULL,
  `units_used` float NOT NULL,
  `inventory_id` int NOT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `transfusion_id` (`transfusion_id`),
  KEY `inventory_id` (`inventory_id`),
  CONSTRAINT `blood_transfusion_items_ibfk_1` FOREIGN KEY (`transfusion_id`) REFERENCES `blood_transfusions` (`id`),
  CONSTRAINT `blood_transfusion_items_ibfk_2` FOREIGN KEY (`inventory_id`) REFERENCES `blood_inventory` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blood_transfusion_items`
--

LOCK TABLES `blood_transfusion_items` WRITE;
/*!40000 ALTER TABLE `blood_transfusion_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `blood_transfusion_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `blood_transfusions`
--

DROP TABLE IF EXISTS `blood_transfusions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `blood_transfusions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transfusion_date` datetime NOT NULL,
  `patient_id` int NOT NULL,
  `doctor_id` int NOT NULL,
  `notes` text,
  `adverse_reaction` tinyint(1) DEFAULT NULL,
  `reaction_details` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `patient_id` (`patient_id`),
  KEY `doctor_id` (`doctor_id`),
  CONSTRAINT `blood_transfusions_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`),
  CONSTRAINT `blood_transfusions_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `blood_transfusions`
--

LOCK TABLES `blood_transfusions` WRITE;
/*!40000 ALTER TABLE `blood_transfusions` DISABLE KEYS */;
/*!40000 ALTER TABLE `blood_transfusions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `charge_category`
--

DROP TABLE IF EXISTS `charge_category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `charge_category` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `charge_category`
--

LOCK TABLES `charge_category` WRITE;
/*!40000 ALTER TABLE `charge_category` DISABLE KEYS */;
/*!40000 ALTER TABLE `charge_category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `charge_item`
--

DROP TABLE IF EXISTS `charge_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `charge_item` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `standard_charge` float NOT NULL,
  `category_id` int DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `charge_item_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `charge_category` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `charge_item`
--

LOCK TABLES `charge_item` WRITE;
/*!40000 ALTER TABLE `charge_item` DISABLE KEYS */;
/*!40000 ALTER TABLE `charge_item` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `child_cases`
--

DROP TABLE IF EXISTS `child_cases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `child_cases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `case_number` varchar(20) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `gender` varchar(10) NOT NULL,
  `birth_date` date NOT NULL,
  `address` varchar(200) NOT NULL,
  `mother_name` varchar(100) NOT NULL,
  `father_name` varchar(100) NOT NULL,
  `father_email` varchar(100) NOT NULL,
  `contact_number` varchar(20) NOT NULL,
  `status` varchar(20) DEFAULT NULL,
  `case_notes` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `case_number` (`case_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `child_cases`
--

LOCK TABLES `child_cases` WRITE;
/*!40000 ALTER TABLE `child_cases` DISABLE KEYS */;
/*!40000 ALTER TABLE `child_cases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `communication_requests`
--

DROP TABLE IF EXISTS `communication_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `communication_requests` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sender_id` int NOT NULL,
  `receiver_id` int NOT NULL,
  `status` enum('pending','accepted','rejected') DEFAULT NULL,
  `message` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sender_id` (`sender_id`),
  KEY `receiver_id` (`receiver_id`),
  CONSTRAINT `communication_requests_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`),
  CONSTRAINT `communication_requests_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `communication_requests`
--

LOCK TABLES `communication_requests` WRITE;
/*!40000 ALTER TABLE `communication_requests` DISABLE KEYS */;
/*!40000 ALTER TABLE `communication_requests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `coverage_types`
--

DROP TABLE IF EXISTS `coverage_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `coverage_types` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `coverage_types`
--

LOCK TABLES `coverage_types` WRITE;
/*!40000 ALTER TABLE `coverage_types` DISABLE KEYS */;
/*!40000 ALTER TABLE `coverage_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `death_records`
--

DROP TABLE IF EXISTS `death_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `death_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `case_number` varchar(20) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `gender` varchar(10) NOT NULL,
  `birth_date` date DEFAULT NULL,
  `death_date` date NOT NULL,
  `death_time` time DEFAULT NULL,
  `email` varchar(100) NOT NULL,
  `place_of_death` varchar(255) DEFAULT NULL,
  `relationship` varchar(255) DEFAULT NULL,
  `address` varchar(200) DEFAULT NULL,
  `cause_of_death` varchar(100) NOT NULL,
  `guardian_name` varchar(100) DEFAULT NULL,
  `contact_number` varchar(20) DEFAULT NULL,
  `notes` text,
  `certificate_issue_date` datetime DEFAULT NULL,
  `death_certificate_issued` tinyint(1) DEFAULT NULL,
  `pronounced_by` int DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `case_number` (`case_number`),
  KEY `ix_death_records_pronounced_by` (`pronounced_by`),
  CONSTRAINT `death_records_ibfk_1` FOREIGN KEY (`pronounced_by`) REFERENCES `doctor` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `death_records`
--

LOCK TABLES `death_records` WRITE;
/*!40000 ALTER TABLE `death_records` DISABLE KEYS */;
/*!40000 ALTER TABLE `death_records` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `department_assignments`
--

DROP TABLE IF EXISTS `department_assignments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `department_assignments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `doctor_id` int NOT NULL,
  `department_id` int NOT NULL,
  `specialty` varchar(100) DEFAULT NULL,
  `assigned_date` date DEFAULT NULL,
  `experience_level` enum('Junior','Mid-level','Senior') DEFAULT NULL,
  `current_status` enum('Active','On Leave','Inactive','Pending') DEFAULT NULL,
  `notes` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `doctor_id` (`doctor_id`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `department_assignments_ibfk_1` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`),
  CONSTRAINT `department_assignments_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `department_assignments`
--

LOCK TABLES `department_assignments` WRITE;
/*!40000 ALTER TABLE `department_assignments` DISABLE KEYS */;
/*!40000 ALTER TABLE `department_assignments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `department_heads`
--

DROP TABLE IF EXISTS `department_heads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `department_heads` (
  `id` int NOT NULL AUTO_INCREMENT,
  `department_id` int NOT NULL,
  `doctor_id` int NOT NULL,
  `start_date` datetime DEFAULT (now()),
  `end_date` datetime DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `department_id` (`department_id`),
  KEY `doctor_id` (`doctor_id`),
  CONSTRAINT `department_heads_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`),
  CONSTRAINT `department_heads_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `department_heads`
--

LOCK TABLES `department_heads` WRITE;
/*!40000 ALTER TABLE `department_heads` DISABLE KEYS */;
/*!40000 ALTER TABLE `department_heads` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `departments`
--

DROP TABLE IF EXISTS `departments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `departments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `status` varchar(10) NOT NULL,
  `message` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `departments`
--

LOCK TABLES `departments` WRITE;
/*!40000 ALTER TABLE `departments` DISABLE KEYS */;
/*!40000 ALTER TABLE `departments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `doctor`
--

DROP TABLE IF EXISTS `doctor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `doctor` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `doctor_id` int NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `age` int NOT NULL,
  `gender` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `qualification` varchar(100) DEFAULT NULL,
  `designation` varchar(100) DEFAULT NULL,
  `blood_group` varchar(100) DEFAULT NULL,
  `address` varchar(100) DEFAULT NULL,
  `bio` text,
  `profile_picture` varchar(200) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `doctor_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctor`
--

LOCK TABLES `doctor` WRITE;
/*!40000 ALTER TABLE `doctor` DISABLE KEYS */;
/*!40000 ALTER TABLE `doctor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `driver`
--

DROP TABLE IF EXISTS `driver`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `driver` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `license_number` varchar(50) NOT NULL,
  `contact` varchar(20) NOT NULL,
  `address` text NOT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `emergency_contact` varchar(20) DEFAULT NULL,
  `blood_group` varchar(5) DEFAULT NULL,
  `license_expiry` date DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `license_number` (`license_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `driver`
--

LOCK TABLES `driver` WRITE;
/*!40000 ALTER TABLE `driver` DISABLE KEYS */;
/*!40000 ALTER TABLE `driver` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `insurance_claims`
--

DROP TABLE IF EXISTS `insurance_claims`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `insurance_claims` (
  `id` int NOT NULL AUTO_INCREMENT,
  `claim_id` varchar(20) NOT NULL,
  `patient_id` varchar(20) NOT NULL,
  `patient_name` varchar(100) NOT NULL,
  `service_date` date NOT NULL,
  `claim_date` date NOT NULL,
  `diagnosis_code` varchar(20) NOT NULL,
  `procedure_code` varchar(20) NOT NULL,
  `service_description` text NOT NULL,
  `claim_amount` decimal(12,2) NOT NULL,
  `claim_type` varchar(20) NOT NULL,
  `approved_amount` decimal(12,2) DEFAULT NULL,
  `deductible` decimal(10,2) DEFAULT NULL,
  `copayment` decimal(10,2) DEFAULT NULL,
  `patient_responsibility` decimal(10,2) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `documents` text,
  `remarks` text,
  `processed_date` date DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  `created_by` int NOT NULL,
  `insurance_provider_id` int DEFAULT NULL,
  `insurance_record_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `claim_id` (`claim_id`),
  KEY `created_by` (`created_by`),
  KEY `insurance_provider_id` (`insurance_provider_id`),
  KEY `insurance_record_id` (`insurance_record_id`),
  CONSTRAINT `insurance_claims_ibfk_1` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`),
  CONSTRAINT `insurance_claims_ibfk_2` FOREIGN KEY (`insurance_provider_id`) REFERENCES `insurance_providers` (`id`),
  CONSTRAINT `insurance_claims_ibfk_3` FOREIGN KEY (`insurance_record_id`) REFERENCES `insurance_records` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `insurance_claims`
--

LOCK TABLES `insurance_claims` WRITE;
/*!40000 ALTER TABLE `insurance_claims` DISABLE KEYS */;
/*!40000 ALTER TABLE `insurance_claims` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `insurance_providers`
--

DROP TABLE IF EXISTS `insurance_providers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `insurance_providers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `code` varchar(20) NOT NULL,
  `website` varchar(100) DEFAULT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(100) NOT NULL,
  `support_phone` varchar(20) DEFAULT NULL,
  `address` text,
  `contract_start` date NOT NULL,
  `contract_end` date NOT NULL,
  `reimbursement_rate` float NOT NULL,
  `payment_terms` varchar(100) DEFAULT NULL,
  `notes` text,
  `status` varchar(20) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `insurance_providers`
--

LOCK TABLES `insurance_providers` WRITE;
/*!40000 ALTER TABLE `insurance_providers` DISABLE KEYS */;
/*!40000 ALTER TABLE `insurance_providers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `insurance_records`
--

DROP TABLE IF EXISTS `insurance_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `insurance_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `insurance_id` varchar(20) NOT NULL,
  `patient_id` varchar(20) NOT NULL,
  `patient_name` varchar(100) NOT NULL,
  `policy_number` varchar(50) NOT NULL,
  `policy_type` varchar(20) NOT NULL,
  `coverage_start` date NOT NULL,
  `coverage_end` date NOT NULL,
  `coverage_amount` decimal(12,2) NOT NULL,
  `copayment` decimal(5,2) DEFAULT NULL,
  `status` varchar(20) NOT NULL,
  `remarks` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  `insurance_provider_id` int DEFAULT NULL,
  `patient_user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `insurance_id` (`insurance_id`),
  KEY `insurance_provider_id` (`insurance_provider_id`),
  KEY `patient_user_id` (`patient_user_id`),
  CONSTRAINT `insurance_records_ibfk_1` FOREIGN KEY (`insurance_provider_id`) REFERENCES `insurance_providers` (`id`),
  CONSTRAINT `insurance_records_ibfk_2` FOREIGN KEY (`patient_user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `insurance_records`
--

LOCK TABLES `insurance_records` WRITE;
/*!40000 ALTER TABLE `insurance_records` DISABLE KEYS */;
/*!40000 ALTER TABLE `insurance_records` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventory_items`
--

DROP TABLE IF EXISTS `inventory_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventory_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_name` varchar(100) NOT NULL,
  `category_id` int NOT NULL,
  `description` text,
  `min_quantity` int DEFAULT NULL,
  `is_restricted` tinyint(1) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `category_id` (`category_id`),
  CONSTRAINT `inventory_items_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `item_categories` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventory_items`
--

LOCK TABLES `inventory_items` WRITE;
/*!40000 ALTER TABLE `inventory_items` DISABLE KEYS */;
INSERT INTO `inventory_items` VALUES (1,'Manual Wheelchairs',9,'A user-powered wheelchair that can be pushed from behind by an assistant',250,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(2,'Operating Scissors',8,'Scissors for general or surgical purposes in various sizes',200,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(3,'Glucose Monitor',3,'Device for measuring blood sugar levels',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(4,'Surgical Blade',6,'Used for surgical incisions with precision',500,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(5,'PPE Kit',3,'Protective kit for preventing infections',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(6,'Surgical Lights',3,'Lights for illuminating surgical areas',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(7,'Syringe Pump',3,'Delivers fluids into a patient’s body in controlled amounts',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(8,'Endoscope',3,'Used for internal body examination',50,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(9,'Hospital Uniform',5,'Used by staff and patients to maintain hospital standards',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(10,'Patient Bed Sheet',4,'Clean linen for patient beds',500,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(11,'Pharmacy Cabinet',3,'Storage cabinet for medicines and tools',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(12,'Dressing Cotton',2,'Cotton used for dressing wounds',1000,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(13,'Disposable Syringe',1,'For injecting or withdrawing fluids',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(14,'Oxygen Cylinder',3,'Provides supplemental oxygen',200,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(15,'IV Stand',3,'Stands to hold IV fluid bottles',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(16,'Wheelchair Cushion',9,'Provides comfort to wheelchair users',50,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(17,'Dental Mirror',3,'Tool for viewing oral cavity',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(18,'Surgical Table',3,'Table used during surgical operations',50,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(19,'Glucometer Strips',3,'Strips used with glucose monitor',200,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(20,'Surgical Drapes',6,'Sterile drapes for surgeries',500,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(21,'Wound Dressing Kit',2,'Kit with materials for wound care',300,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(22,'Thermometer',3,'Measures body temperature',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(23,'Pulse Oximeter',3,'Measures oxygen saturation in blood',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(24,'Orthopedic Pillow',9,'Used for spinal support in beds/wheelchairs',50,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(25,'Emergency Light',3,'Backup lighting for operation rooms',50,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(26,'Bedside Locker',4,'Locker for patient belongings near the bed',100,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL),(27,'Sterile Gauze',2,'Cotton gauze for wound care',400,0,0,'2025-06-11 16:32:45','2025-06-11 16:32:45',NULL);
/*!40000 ALTER TABLE `inventory_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `issued_items`
--

DROP TABLE IF EXISTS `issued_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `issued_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_id` int NOT NULL,
  `issued_to_name` varchar(100) NOT NULL,
  `issued_to_user_id` varchar(50) DEFAULT NULL,
  `user_type` varchar(50) NOT NULL,
  `issued_by` varchar(100) NOT NULL,
  `issue_date` date NOT NULL,
  `return_date` date DEFAULT NULL,
  `quantity` int NOT NULL,
  `status` varchar(20) DEFAULT NULL,
  `note` text,
  `requested_by` varchar(100) DEFAULT NULL,
  `approved_by` varchar(100) DEFAULT NULL,
  `department` varchar(100) DEFAULT NULL,
  `purpose` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `item_id` (`item_id`),
  CONSTRAINT `issued_items_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `inventory_items` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `issued_items`
--

LOCK TABLES `issued_items` WRITE;
/*!40000 ALTER TABLE `issued_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `issued_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `item_categories`
--

DROP TABLE IF EXISTS `item_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `item_categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `item_categories`
--

LOCK TABLES `item_categories` WRITE;
/*!40000 ALTER TABLE `item_categories` DISABLE KEYS */;
INSERT INTO `item_categories` VALUES (1,'Syringe Packs','Sterile packs of disposable syringes',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(2,'Cotton Packs','Medical-grade cotton used for wound cleaning',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(3,'Medical Equipment','General medical tools and devices',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(4,'Bed Sheets','Linen used on hospital beds',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(5,'Uniforms','Hospital staff clothing',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(6,'Surgical Blades','Sharp blades for surgical procedures',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(7,'Automatic BP Cuff','Digital blood pressure monitoring device',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(8,'Medical Scissors','Scissors used for medical applications',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(9,'Patient Wheelchairs','Mobile chairs for patient transportation',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(10,'Clinical Stools','Stools used by doctors or staff during examinations',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(11,'Medical Apparel','Wearables like scrubs and lab coats',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(12,'Cardiology Equipment','Tools for heart monitoring and treatment',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(13,'IV Stands','Stands used for hanging IV fluids',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(14,'Defibrillators','Devices to restore normal heartbeat during emergencies',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(15,'Examination Gloves','Disposable gloves for examinations',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(16,'Face Masks','Protective masks used in hospital environments',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(17,'Thermometers','Devices to measure body temperature',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(18,'Stethoscopes','Tool for listening to internal body sounds',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(19,'Oxygen Cylinders','Portable oxygen supply units',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(20,'Nebulizers','Devices for delivering medication via inhalation',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(21,'Surgical Drapes','Sterile coverings used during surgeries',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(22,'Hospital Stretchers','Wheeled beds for patient transport',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(23,'Hospital Gowns','Gowns worn by patients during hospital stays',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(24,'Surgical Lights','Overhead lighting for operating rooms',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(25,'ECG Machines','Devices to record heart electrical activity',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(26,'X-Ray Film Packs','Films used for capturing radiographic images',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(27,'Urine Collection Bags','Bags used to collect urine via catheter',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(28,'Orthopedic Supports','Supports for injured joints and limbs',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(29,'Dental Kits','Instruments used for dental treatment',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL),(30,'Sanitizer Dispensers','Wall-mounted or stand sanitizers for hygiene',0,'2025-06-11 16:32:29','2025-06-11 16:32:29',NULL);
/*!40000 ALTER TABLE `item_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `item_stocks`
--

DROP TABLE IF EXISTS `item_stocks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `item_stocks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `item_id` int NOT NULL,
  `supplier_id` int NOT NULL,
  `store_id` int NOT NULL,
  `quantity` int NOT NULL,
  `purchase_price` float NOT NULL,
  `purchase_date` date NOT NULL,
  `selling_price` float DEFAULT NULL,
  `batch_number` varchar(100) DEFAULT NULL,
  `manufacture_date` datetime DEFAULT NULL,
  `expiry_date` datetime DEFAULT NULL,
  `description` text,
  `document_path` varchar(255) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `item_id` (`item_id`),
  KEY `supplier_id` (`supplier_id`),
  KEY `store_id` (`store_id`),
  CONSTRAINT `item_stocks_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `inventory_items` (`id`),
  CONSTRAINT `item_stocks_ibfk_2` FOREIGN KEY (`supplier_id`) REFERENCES `item_suppliers` (`id`),
  CONSTRAINT `item_stocks_ibfk_3` FOREIGN KEY (`store_id`) REFERENCES `item_stores` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `item_stocks`
--

LOCK TABLES `item_stocks` WRITE;
/*!40000 ALTER TABLE `item_stocks` DISABLE KEYS */;
/*!40000 ALTER TABLE `item_stocks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `item_stores`
--

DROP TABLE IF EXISTS `item_stores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `item_stores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `stock_code` varchar(50) DEFAULT NULL,
  `description` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `item_stores`
--

LOCK TABLES `item_stores` WRITE;
/*!40000 ALTER TABLE `item_stores` DISABLE KEYS */;
/*!40000 ALTER TABLE `item_stores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `item_suppliers`
--

DROP TABLE IF EXISTS `item_suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `item_suppliers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `contact_person_name` varchar(100) DEFAULT NULL,
  `address` text,
  `contact_person_phone` varchar(20) DEFAULT NULL,
  `contact_person_email` varchar(100) DEFAULT NULL,
  `description` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `item_suppliers`
--

LOCK TABLES `item_suppliers` WRITE;
/*!40000 ALTER TABLE `item_suppliers` DISABLE KEYS */;
/*!40000 ALTER TABLE `item_suppliers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `laboratory_test_reports`
--

DROP TABLE IF EXISTS `laboratory_test_reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `laboratory_test_reports` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text,
  `price` float NOT NULL,
  `department_id` int NOT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `laboratory_test_reports_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `laboratory_test_reports`
--

LOCK TABLES `laboratory_test_reports` WRITE;
/*!40000 ALTER TABLE `laboratory_test_reports` DISABLE KEYS */;
/*!40000 ALTER TABLE `laboratory_test_reports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medical_visits`
--

DROP TABLE IF EXISTS `medical_visits`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medical_visits` (
  `id` int NOT NULL AUTO_INCREMENT,
  `child_case_id` int NOT NULL,
  `visit_date` date NOT NULL,
  `visit_type` varchar(50) NOT NULL,
  `height` varchar(10) DEFAULT NULL,
  `weight` varchar(10) DEFAULT NULL,
  `notes` text,
  `doctor_id` int DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `child_case_id` (`child_case_id`),
  KEY `doctor_id` (`doctor_id`),
  CONSTRAINT `medical_visits_ibfk_1` FOREIGN KEY (`child_case_id`) REFERENCES `child_cases` (`id`),
  CONSTRAINT `medical_visits_ibfk_2` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medical_visits`
--

LOCK TABLES `medical_visits` WRITE;
/*!40000 ALTER TABLE `medical_visits` DISABLE KEYS */;
/*!40000 ALTER TABLE `medical_visits` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medication_timings`
--

DROP TABLE IF EXISTS `medication_timings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medication_timings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `medication_id` int NOT NULL,
  `timing` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `medication_id` (`medication_id`),
  CONSTRAINT `medication_timings_ibfk_1` FOREIGN KEY (`medication_id`) REFERENCES `prescription_medications` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medication_timings`
--

LOCK TABLES `medication_timings` WRITE;
/*!40000 ALTER TABLE `medication_timings` DISABLE KEYS */;
/*!40000 ALTER TABLE `medication_timings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medicine_batches`
--

DROP TABLE IF EXISTS `medicine_batches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medicine_batches` (
  `id` int NOT NULL AUTO_INCREMENT,
  `medicine_id` int NOT NULL,
  `purchase_item_id` int DEFAULT NULL,
  `batch_no` varchar(50) NOT NULL,
  `expiry_date` date NOT NULL,
  `purchase_price` decimal(10,2) NOT NULL,
  `selling_price` decimal(10,2) NOT NULL,
  `mrp` decimal(10,2) NOT NULL,
  `tax_rate` decimal(5,2) DEFAULT NULL,
  `initial_quantity` int NOT NULL,
  `current_stock` int NOT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `medicine_id` (`medicine_id`),
  KEY `purchase_item_id` (`purchase_item_id`),
  CONSTRAINT `medicine_batches_ibfk_1` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`id`),
  CONSTRAINT `medicine_batches_ibfk_2` FOREIGN KEY (`purchase_item_id`) REFERENCES `purchase_items` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medicine_batches`
--

LOCK TABLES `medicine_batches` WRITE;
/*!40000 ALTER TABLE `medicine_batches` DISABLE KEYS */;
/*!40000 ALTER TABLE `medicine_batches` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medicine_categories`
--

DROP TABLE IF EXISTS `medicine_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medicine_categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medicine_categories`
--

LOCK TABLES `medicine_categories` WRITE;
/*!40000 ALTER TABLE `medicine_categories` DISABLE KEYS */;
/*!40000 ALTER TABLE `medicine_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medicine_companies`
--

DROP TABLE IF EXISTS `medicine_companies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medicine_companies` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `address` text,
  `contact_number` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `website` varchar(255) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medicine_companies`
--

LOCK TABLES `medicine_companies` WRITE;
/*!40000 ALTER TABLE `medicine_companies` DISABLE KEYS */;
/*!40000 ALTER TABLE `medicine_companies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medicine_groups`
--

DROP TABLE IF EXISTS `medicine_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medicine_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `description` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medicine_groups`
--

LOCK TABLES `medicine_groups` WRITE;
/*!40000 ALTER TABLE `medicine_groups` DISABLE KEYS */;
INSERT INTO `medicine_groups` VALUES (1,'Antibiotics','Used to treat bacterial infections',0,'2025-06-11 16:29:54','2025-06-11 16:29:54'),(2,'Analgesics','Pain relievers',0,'2025-06-11 16:29:54','2025-06-11 16:29:54'),(3,'Antipyretics','Used to reduce fever',0,'2025-06-11 16:29:54','2025-06-11 16:29:54'),(4,'Antiseptics','Prevent the growth of disease-causing microorganisms',0,'2025-06-11 16:29:54','2025-06-11 16:29:54'),(5,'Antacids','Neutralize stomach acidity',0,'2025-06-11 16:29:54','2025-06-11 16:29:54');
/*!40000 ALTER TABLE `medicine_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medicine_purchases`
--

DROP TABLE IF EXISTS `medicine_purchases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medicine_purchases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bill_no` varchar(20) NOT NULL,
  `purchase_date` datetime NOT NULL DEFAULT (now()),
  `supplier_id` int NOT NULL,
  `subtotal` decimal(10,2) DEFAULT NULL,
  `discount_percent` decimal(5,2) DEFAULT NULL,
  `discount_amount` decimal(10,2) DEFAULT NULL,
  `tax_amount` decimal(10,2) DEFAULT NULL,
  `total_amount` decimal(10,2) DEFAULT NULL,
  `paid_amount` decimal(10,2) DEFAULT NULL,
  `due_amount` decimal(10,2) DEFAULT NULL,
  `payment_mode` varchar(20) DEFAULT NULL,
  `payment_note` text,
  `note` text,
  `attachment` varchar(255) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `created_by` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bill_no` (`bill_no`),
  KEY `supplier_id` (`supplier_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `medicine_purchases_ibfk_1` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`),
  CONSTRAINT `medicine_purchases_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medicine_purchases`
--

LOCK TABLES `medicine_purchases` WRITE;
/*!40000 ALTER TABLE `medicine_purchases` DISABLE KEYS */;
/*!40000 ALTER TABLE `medicine_purchases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medicine_sale_items`
--

DROP TABLE IF EXISTS `medicine_sale_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medicine_sale_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sale_id` int NOT NULL,
  `medicine_id` int NOT NULL,
  `batch_id` int NOT NULL,
  `quantity` int NOT NULL,
  `sale_price` decimal(10,2) NOT NULL,
  `tax_rate` decimal(5,2) DEFAULT NULL,
  `amount` decimal(10,2) NOT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sale_id` (`sale_id`),
  KEY `medicine_id` (`medicine_id`),
  KEY `batch_id` (`batch_id`),
  CONSTRAINT `medicine_sale_items_ibfk_1` FOREIGN KEY (`sale_id`) REFERENCES `medicine_sales` (`id`),
  CONSTRAINT `medicine_sale_items_ibfk_2` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`id`),
  CONSTRAINT `medicine_sale_items_ibfk_3` FOREIGN KEY (`batch_id`) REFERENCES `medicine_batches` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medicine_sale_items`
--

LOCK TABLES `medicine_sale_items` WRITE;
/*!40000 ALTER TABLE `medicine_sale_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `medicine_sale_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medicine_sales`
--

DROP TABLE IF EXISTS `medicine_sales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medicine_sales` (
  `id` int NOT NULL AUTO_INCREMENT,
  `prescription_no` varchar(50) DEFAULT NULL,
  `patient_id` int NOT NULL,
  `bill_no` varchar(50) NOT NULL,
  `case_id` varchar(50) DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  `doctor_id` int DEFAULT NULL,
  `note` text,
  `total_amount` decimal(10,2) DEFAULT NULL,
  `discount_amount` decimal(10,2) DEFAULT NULL,
  `tax_amount` decimal(10,2) DEFAULT NULL,
  `net_amount` decimal(10,2) DEFAULT NULL,
  `payment_mode` varchar(20) DEFAULT NULL,
  `payment_amount` decimal(10,2) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  `created_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bill_no` (`bill_no`),
  UNIQUE KEY `prescription_no` (`prescription_no`),
  KEY `doctor_id` (`doctor_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `medicine_sales_ibfk_1` FOREIGN KEY (`doctor_id`) REFERENCES `doctor` (`id`),
  CONSTRAINT `medicine_sales_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medicine_sales`
--

LOCK TABLES `medicine_sales` WRITE;
/*!40000 ALTER TABLE `medicine_sales` DISABLE KEYS */;
/*!40000 ALTER TABLE `medicine_sales` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medicines`
--

DROP TABLE IF EXISTS `medicines`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `medicines` (
  `id` int NOT NULL AUTO_INCREMENT,
  `medicine_number` varchar(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  `composition` text,
  `category_id` int DEFAULT NULL,
  `company_id` int DEFAULT NULL,
  `group_id` int DEFAULT NULL,
  `unit_id` int DEFAULT NULL,
  `min_level` int DEFAULT NULL,
  `reorder_level` int DEFAULT NULL,
  `box_packing` int DEFAULT NULL,
  `rack_number` varchar(20) DEFAULT NULL,
  `default_tax_rate` decimal(5,2) DEFAULT NULL,
  `vat_account` varchar(50) DEFAULT NULL,
  `default_purchase_price` decimal(10,2) DEFAULT NULL,
  `default_selling_price` decimal(10,2) DEFAULT NULL,
  `default_mrp` decimal(10,2) DEFAULT NULL,
  `barcode` varchar(100) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `medicine_number` (`medicine_number`),
  UNIQUE KEY `barcode` (`barcode`),
  KEY `category_id` (`category_id`),
  KEY `company_id` (`company_id`),
  KEY `group_id` (`group_id`),
  KEY `unit_id` (`unit_id`),
  CONSTRAINT `medicines_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `medicine_categories` (`id`),
  CONSTRAINT `medicines_ibfk_2` FOREIGN KEY (`company_id`) REFERENCES `medicine_companies` (`id`),
  CONSTRAINT `medicines_ibfk_3` FOREIGN KEY (`group_id`) REFERENCES `medicine_groups` (`id`),
  CONSTRAINT `medicines_ibfk_4` FOREIGN KEY (`unit_id`) REFERENCES `units` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medicines`
--

LOCK TABLES `medicines` WRITE;
/*!40000 ALTER TABLE `medicines` DISABLE KEYS */;
/*!40000 ALTER TABLE `medicines` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sender_id` int NOT NULL,
  `receiver_id` int NOT NULL,
  `message` text NOT NULL,
  `read_status` tinyint(1) DEFAULT NULL,
  `sent_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `sender_id` (`sender_id`),
  KEY `receiver_id` (`receiver_id`),
  CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`),
  CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notice_departments`
--

DROP TABLE IF EXISTS `notice_departments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notice_departments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `notice_id` int DEFAULT NULL,
  `department_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `notice_id` (`notice_id`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `notice_departments_ibfk_1` FOREIGN KEY (`notice_id`) REFERENCES `notices` (`id`) ON DELETE CASCADE,
  CONSTRAINT `notice_departments_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notice_departments`
--

LOCK TABLES `notice_departments` WRITE;
/*!40000 ALTER TABLE `notice_departments` DISABLE KEYS */;
/*!40000 ALTER TABLE `notice_departments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notices`
--

DROP TABLE IF EXISTS `notices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(200) DEFAULT NULL,
  `content` text,
  `posted_by` int DEFAULT NULL,
  `post_date` datetime DEFAULT NULL,
  `expiry_date` datetime DEFAULT NULL,
  `priority` enum('high','medium','low') NOT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `attachment` varchar(255) DEFAULT NULL,
  `target_type` enum('role','department') NOT NULL,
  `roles` json DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `posted_by` (`posted_by`),
  CONSTRAINT `notices_ibfk_1` FOREIGN KEY (`posted_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notices`
--

LOCK TABLES `notices` WRITE;
/*!40000 ALTER TABLE `notices` DISABLE KEYS */;
/*!40000 ALTER TABLE `notices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `message` text NOT NULL,
  `type` varchar(50) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `read_status` tinyint(1) DEFAULT NULL,
  `redirect_url` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patient`
--

DROP TABLE IF EXISTS `patient`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patient` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `patient_id` int NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `age` int DEFAULT NULL,
  `address` text,
  `phone` varchar(20) DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `patient_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patient`
--

LOCK TABLES `patient` WRITE;
/*!40000 ALTER TABLE `patient` DISABLE KEYS */;
INSERT INTO `patient` VALUES (1,10,2025061129,'Rahul','Sharma',28,NULL,'9876543210','Male',0,'2025-06-11 16:29:55','2025-06-11 16:29:55',NULL),(2,11,2025061156,'Priya','Verma',34,NULL,'8765432109','Female',0,'2025-06-11 16:29:55','2025-06-11 16:29:55',NULL),(3,12,2025061165,'Amit','Patel',45,NULL,'7654321098','Male',0,'2025-06-11 16:29:55','2025-06-11 16:29:55',NULL),(4,13,2025061161,'Sneha','Kumar',23,NULL,'6543210987','Female',0,'2025-06-11 16:29:55','2025-06-11 16:29:55',NULL),(5,14,2025061122,'Deepak','Joshi',37,NULL,'5432109876','Male',0,'2025-06-11 16:29:55','2025-06-11 16:29:55',NULL);
/*!40000 ALTER TABLE `patient` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patient_payment`
--

DROP TABLE IF EXISTS `patient_payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patient_payment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `patient_id` int NOT NULL,
  `room_charge_id` int DEFAULT NULL,
  `amount` float NOT NULL,
  `status` varchar(20) DEFAULT NULL,
  `payment_date` datetime DEFAULT NULL,
  `remarks` varchar(255) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `patient_id` (`patient_id`),
  KEY `room_charge_id` (`room_charge_id`),
  CONSTRAINT `patient_payment_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`),
  CONSTRAINT `patient_payment_ibfk_2` FOREIGN KEY (`room_charge_id`) REFERENCES `room_charge` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patient_payment`
--

LOCK TABLES `patient_payment` WRITE;
/*!40000 ALTER TABLE `patient_payment` DISABLE KEYS */;
/*!40000 ALTER TABLE `patient_payment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prescription_medications`
--

DROP TABLE IF EXISTS `prescription_medications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prescription_medications` (
  `id` int NOT NULL AUTO_INCREMENT,
  `prescription_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `dosage` varchar(50) NOT NULL,
  `meal_instructions` varchar(50) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `prescription_id` (`prescription_id`),
  CONSTRAINT `prescription_medications_ibfk_1` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prescription_medications`
--

LOCK TABLES `prescription_medications` WRITE;
/*!40000 ALTER TABLE `prescription_medications` DISABLE KEYS */;
/*!40000 ALTER TABLE `prescription_medications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prescription_test_reports`
--

DROP TABLE IF EXISTS `prescription_test_reports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prescription_test_reports` (
  `id` int NOT NULL AUTO_INCREMENT,
  `prescription_id` int NOT NULL,
  `lab_report_id` int DEFAULT NULL,
  `report_name` varchar(255) NOT NULL,
  `report_notes` text,
  `price` float NOT NULL,
  `status` varchar(20) DEFAULT NULL,
  `file_path` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `prescription_id` (`prescription_id`),
  KEY `lab_report_id` (`lab_report_id`),
  CONSTRAINT `prescription_test_reports_ibfk_1` FOREIGN KEY (`prescription_id`) REFERENCES `prescriptions` (`id`),
  CONSTRAINT `prescription_test_reports_ibfk_2` FOREIGN KEY (`lab_report_id`) REFERENCES `laboratory_test_reports` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prescription_test_reports`
--

LOCK TABLES `prescription_test_reports` WRITE;
/*!40000 ALTER TABLE `prescription_test_reports` DISABLE KEYS */;
/*!40000 ALTER TABLE `prescription_test_reports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `prescriptions`
--

DROP TABLE IF EXISTS `prescriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prescriptions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `appointment_id` int NOT NULL,
  `notes` text,
  `status` varchar(20) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `appointment_id` (`appointment_id`),
  CONSTRAINT `prescriptions_ibfk_1` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `prescriptions`
--

LOCK TABLES `prescriptions` WRITE;
/*!40000 ALTER TABLE `prescriptions` DISABLE KEYS */;
/*!40000 ALTER TABLE `prescriptions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `provider_coverage`
--

DROP TABLE IF EXISTS `provider_coverage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `provider_coverage` (
  `provider_id` int NOT NULL,
  `coverage_id` int NOT NULL,
  PRIMARY KEY (`provider_id`,`coverage_id`),
  KEY `coverage_id` (`coverage_id`),
  CONSTRAINT `provider_coverage_ibfk_1` FOREIGN KEY (`provider_id`) REFERENCES `insurance_providers` (`id`),
  CONSTRAINT `provider_coverage_ibfk_2` FOREIGN KEY (`coverage_id`) REFERENCES `coverage_types` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `provider_coverage`
--

LOCK TABLES `provider_coverage` WRITE;
/*!40000 ALTER TABLE `provider_coverage` DISABLE KEYS */;
/*!40000 ALTER TABLE `provider_coverage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchase_items`
--

DROP TABLE IF EXISTS `purchase_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `purchase_id` int NOT NULL,
  `medicine_id` int NOT NULL,
  `batch_no` varchar(50) NOT NULL,
  `expiry_date` date NOT NULL,
  `packing_qty` int DEFAULT NULL,
  `quantity` int NOT NULL,
  `mrp` decimal(10,2) NOT NULL,
  `purchase_price` decimal(10,2) NOT NULL,
  `sale_price` decimal(10,2) NOT NULL,
  `tax_rate` decimal(5,2) DEFAULT NULL,
  `tax_amount` decimal(10,2) DEFAULT NULL,
  `amount` decimal(10,2) NOT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `purchase_id` (`purchase_id`),
  KEY `medicine_id` (`medicine_id`),
  CONSTRAINT `purchase_items_ibfk_1` FOREIGN KEY (`purchase_id`) REFERENCES `medicine_purchases` (`id`),
  CONSTRAINT `purchase_items_ibfk_2` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchase_items`
--

LOCK TABLES `purchase_items` WRITE;
/*!40000 ALTER TABLE `purchase_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `purchase_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `room`
--

DROP TABLE IF EXISTS `room`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `room` (
  `id` int NOT NULL AUTO_INCREMENT,
  `room_number` varchar(10) NOT NULL,
  `floor` varchar(10) NOT NULL,
  `room_type` varchar(20) NOT NULL,
  `department_id` int DEFAULT NULL,
  `charge_per_day` float NOT NULL,
  `is_empty` tinyint(1) DEFAULT NULL,
  `message` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `room_number` (`room_number`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `room_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `room`
--

LOCK TABLES `room` WRITE;
/*!40000 ALTER TABLE `room` DISABLE KEYS */;
/*!40000 ALTER TABLE `room` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `room_charge`
--

DROP TABLE IF EXISTS `room_charge`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `room_charge` (
  `id` int NOT NULL AUTO_INCREMENT,
  `room_id` int NOT NULL,
  `bed_id` int NOT NULL,
  `patient_id` int NOT NULL,
  `allocation_id` int DEFAULT NULL,
  `start_date` datetime NOT NULL,
  `end_date` datetime DEFAULT NULL,
  `charge_per_day` float NOT NULL,
  `total_amount` float DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `room_id` (`room_id`),
  KEY `bed_id` (`bed_id`),
  KEY `patient_id` (`patient_id`),
  KEY `allocation_id` (`allocation_id`),
  CONSTRAINT `room_charge_ibfk_1` FOREIGN KEY (`room_id`) REFERENCES `room` (`id`),
  CONSTRAINT `room_charge_ibfk_2` FOREIGN KEY (`bed_id`) REFERENCES `bed` (`id`),
  CONSTRAINT `room_charge_ibfk_3` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`id`),
  CONSTRAINT `room_charge_ibfk_4` FOREIGN KEY (`allocation_id`) REFERENCES `bed_allocation` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `room_charge`
--

LOCK TABLES `room_charge` WRITE;
/*!40000 ALTER TABLE `room_charge` DISABLE KEYS */;
/*!40000 ALTER TABLE `room_charge` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `staff`
--

DROP TABLE IF EXISTS `staff`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `staff` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `mobile` varchar(20) DEFAULT NULL,
  `designation` varchar(100) NOT NULL,
  `department_id` int DEFAULT NULL,
  `joining_date` date NOT NULL,
  `salary` float DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `shift` varchar(20) DEFAULT NULL,
  `experience` int DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `address` text,
  `date_of_birth` date DEFAULT NULL,
  `education` text,
  `profile_picture` varchar(255) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `staff_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `staff_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `staff`
--

LOCK TABLES `staff` WRITE;
/*!40000 ALTER TABLE `staff` DISABLE KEYS */;
/*!40000 ALTER TABLE `staff` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_transactions`
--

DROP TABLE IF EXISTS `stock_transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_transactions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `medicine_id` int NOT NULL,
  `batch_id` int NOT NULL,
  `transaction_type` varchar(20) NOT NULL,
  `quantity` int NOT NULL,
  `balance` int NOT NULL,
  `reference` varchar(100) DEFAULT NULL,
  `notes` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  `created_by` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `medicine_id` (`medicine_id`),
  KEY `batch_id` (`batch_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `stock_transactions_ibfk_1` FOREIGN KEY (`medicine_id`) REFERENCES `medicines` (`id`),
  CONSTRAINT `stock_transactions_ibfk_2` FOREIGN KEY (`batch_id`) REFERENCES `medicine_batches` (`id`),
  CONSTRAINT `stock_transactions_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_transactions`
--

LOCK TABLES `stock_transactions` WRITE;
/*!40000 ALTER TABLE `stock_transactions` DISABLE KEYS */;
/*!40000 ALTER TABLE `stock_transactions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `suppliers`
--

DROP TABLE IF EXISTS `suppliers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `suppliers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `contact_person` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `address` text,
  `tax_id` varchar(50) DEFAULT NULL,
  `payment_terms` text,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `suppliers`
--

LOCK TABLES `suppliers` WRITE;
/*!40000 ALTER TABLE `suppliers` DISABLE KEYS */;
/*!40000 ALTER TABLE `suppliers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `treatments`
--

DROP TABLE IF EXISTS `treatments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `treatments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  `duration_minutes` int DEFAULT NULL,
  `base_price` float NOT NULL,
  `icon` varchar(50) DEFAULT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `department_id` int NOT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `treatments_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `treatments`
--

LOCK TABLES `treatments` WRITE;
/*!40000 ALTER TABLE `treatments` DISABLE KEYS */;
/*!40000 ALTER TABLE `treatments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `units`
--

DROP TABLE IF EXISTS `units`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `units` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(20) NOT NULL,
  `symbol` varchar(10) NOT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT (now()),
  `updated_at` datetime DEFAULT (now()),
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `units`
--

LOCK TABLES `units` WRITE;
/*!40000 ALTER TABLE `units` DISABLE KEYS */;
INSERT INTO `units` VALUES (1,'Tablet','tab',0,'2025-06-11 16:29:54','2025-06-11 16:29:54',NULL),(2,'Capsule','cap',0,'2025-06-11 16:29:54','2025-06-11 16:29:54',NULL),(3,'Syrup','ml',0,'2025-06-11 16:29:54','2025-06-11 16:29:54',NULL),(4,'Injection','inj',0,'2025-06-11 16:29:54','2025-06-11 16:29:54',NULL),(5,'Cream','g',0,'2025-06-11 16:29:54','2025-06-11 16:29:54',NULL);
/*!40000 ALTER TABLE `units` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(100) NOT NULL,
  `password` varchar(200) NOT NULL,
  `role` enum('ADMIN','DOCTOR','ACCOUNTANT','DEPARTMENT_HEAD','PATIENT','STAFF','NURSE','LABORATORIST','RECEPTIONIST') NOT NULL,
  `status` tinyint(1) DEFAULT NULL,
  `verified` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `verification_sent_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin@hospital.com','scrypt:32768:8:1$aBwsPUeimVnst7Vp$c139e66268ac960f58addb450a5d8c5578f6adfcb1dc26ed3c542e55b099e2b7cf762bbd272b585337920dc0bd63738c8862442193b3fa2c98dd674d339ddd97','ADMIN',1,1,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(2,'doctor@hospital.com','scrypt:32768:8:1$oy0LQKIlqJ0s3waC$67341294f6ef2494d29e37b7fe773ee66eae2b9b92e5022d13da3b257bd350768f7c67f572f184ea4655dd950312f8b8281fabefebef668e5012bb39419ea6a5','DOCTOR',1,1,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(3,'accountant@hospital.com','scrypt:32768:8:1$rXb6YzeIlHnO7esS$9b32ce6e5ad8e33b87d371b65a43462825937e792c6e84609a6d1648121ba83a898bd77c42583fb4b9ee12b96fcace1cac1e13c9272fef06883c819fe4448b4b','ACCOUNTANT',1,1,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(4,'department_head@hospital.com','scrypt:32768:8:1$kIaBQqBVFGL00Mjj$50459bca2cdb3ee8ff9b0695d11effdc2930f456900db2775f652354c1712ac84dbec945fff74e33dd3a7ff8d924be5cce23e1b5261d4291e313384ca9cc2527','DEPARTMENT_HEAD',1,1,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(5,'patient@hospital.com','scrypt:32768:8:1$SEYtYae141axzu42$5365c9c9fb59439b1678185a5ee6a79c6a627772e213ec43265fadd70965a789b6db640274c3a170ff35caa97aa3930d3becab1af7fa2e5bdae051753b6f047b','PATIENT',1,1,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(6,'staff@hospital.com','scrypt:32768:8:1$o2DJnMQBDiEfJOlv$19bcefd6c1e842e975f3381ecf6f58c9f7e98133e0385282980b28fee0382eee1e196862d4725a396e5c243180b882c70504c1f118be6c77519597031a87528b','STAFF',1,1,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(7,'nurse@hospital.com','scrypt:32768:8:1$D4WR0lSCtgYVCU8x$a51101feda3bfe03cb64767aef5b8ffa7247a8964ebe51066998838c180d7615562869ca58c7a68eaa47eb284e01020f55d17f60ced69d5625dae0ad47f0e135','NURSE',1,1,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(8,'laboratorist@hospital.com','scrypt:32768:8:1$n6jvAuFtttL2rXyi$63ea7265255feef9043ec9b4f73b5fa5c76bfd3a17315dfacf59b7bc756b23e1c7ef4eb5e47dfbfc8d1646b3f09937addc133264f3149e3af9a24a48f0f4687d','LABORATORIST',1,1,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(9,'receptionist@hospital.com','scrypt:32768:8:1$AjbJyiST3NTyX6w5$30c3583db6dd24bfe46befae7e9e262db0fab4f5a945808d775d5e9fcb45cc2d8704a4fbedebe47a27887f240ffa2a7d710fe36261298dba36d4fff047a31f37','RECEPTIONIST',1,1,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(10,'rahul.sharma@example.com','scrypt:32768:8:1$jOLKolbSyyQJ85Bu$f6f69fba05a29003ceaa44327fdf4bcaf14fe4363086a1bb088844305b52a4c1716b1d3528c20609b81ba5795a4667ce810dec390653f25f8079cba2c7820e4d','PATIENT',1,0,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(11,'priya.verma@example.com','scrypt:32768:8:1$qIAKHOrsNBogR5m0$bc8c6853cae1d1d26b0fd9a9fb519381e433d0b394d6a691a639395b0f4d28ac9a87340c094a650a13383701464ea2e408f14e1be74604421914d8f01000560b','PATIENT',1,0,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(12,'amit.patel@example.com','scrypt:32768:8:1$hae4TpsVx91HIEny$f7addb041bbe745f235eb66473b79e93992f3b87f480be7a654c512f712beb32846e645314eb5730631872d68804255a230272c4b65f9ada264b905fd4e81e4e','PATIENT',1,0,'2025-06-11 10:59:55','2025-06-11 10:59:55','2025-06-11 10:59:55'),(13,'sneha.kumar@example.com','scrypt:32768:8:1$YQBTlhsZexnHBgMo$09b9b46f8dfe9d04653ec97a305efd5198f472672929f2063b8f3123ed7dff476883914172168c214766f1fc292ec419abf4a361fd5049eddbf2728561af27e3','PATIENT',1,0,'2025-06-11 10:59:56','2025-06-11 10:59:56','2025-06-11 10:59:56'),(14,'deepak.joshi@example.com','scrypt:32768:8:1$hvsgiRRmlZxaNm63$a9c6761e04732b5ef015b4a846e7cfa681ef18862dbd93bb1e621617ccfa45cd1c307890bd8a5cdb1ca9fc9a67d8a1356117dffa3de38e6ebb2fb7ab3eba2a54','PATIENT',1,0,'2025-06-11 10:59:56','2025-06-11 10:59:56','2025-06-11 10:59:56');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-06-11 21:02:44
