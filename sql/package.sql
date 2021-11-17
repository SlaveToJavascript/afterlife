-- phpMyAdmin SQL Dump
-- version 4.8.3
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3306
-- Generation Time: Mar 15, 2020 at 07:07 AM
-- Server version: 5.7.23
-- PHP Version: 7.2.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `package`
--

-- --------------------------------------------------------

--
-- Table structure for table `package`
--

DROP TABLE IF EXISTS `package`;
CREATE TABLE IF NOT EXISTS `package` (
  `packagename` varchar(64) NOT NULL,
  `packageid` varchar(64) NOT NULL,
  `packageprice` float(10,2) NOT NULL,
  `packagequantity` int(11) NOT NULL,
  `packagecategory` varchar(64) NOT NULL,
  PRIMARY KEY (`packageid`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `package`
--

INSERT INTO `package` (`packagename`, `packageid`, `packageprice`, `packagequantity`, `packagecategory`) VALUES
('3-day catholic funeral package', 'P1', 4588.00, 10, 'christian'),
('5-day catholic funeral package', 'P2', 5588.00, 10, 'christian'),
('7-day catholic funeral package', 'P3', 6588.00, 0, 'christian'),
('3-day buddhist funeral package', 'P4', 5888.00, 10, 'buddhist'),
('5-day buddhist funeral package', 'P5', 6888.00, 10, 'buddhist'),
('7-day buddhist funeral package', 'P6', 7888.00, 10, 'buddhist'),
('3-day taoist funeral package', 'P7', 8888.00, 10, 'taoist'),
('5-day taoist funeral package', 'P8', 9888.00, 10, 'taoist'),
('7-day taoist funeral package', 'P9', 10888.00, 10, 'taoist');
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
