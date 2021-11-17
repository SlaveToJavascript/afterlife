-- phpMyAdmin SQL Dump
-- version 4.9.3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:8889
-- Generation Time: Mar 27, 2020 at 02:28 PM
-- Server version: 5.7.26
-- PHP Version: 7.4.2

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";

--
-- Database: `corr_id`
--

-- --------------------------------------------------------

--
-- Table structure for table `correlation_id`
--

CREATE TABLE `correlation_id` (
  `supplier_id` varchar(64) NOT NULL,
  `package_id` varchar(64) NOT NULL,
  `quantity` int(11) NOT NULL,
  `correlation_id` varchar(64) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
