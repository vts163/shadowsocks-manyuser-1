CREATE TABLE `ss_user` (
  `id` int(11) NOT NULL,
  `port` int(11) NOT NULL,
  `password` varchar(32) NOT NULL,
  `flow_up` bigint(20) NOT NULL DEFAULT '0',
  `flow_down` bigint(20) NOT NULL DEFAULT '0',
  `transfer_enable` bigint(20) NOT NULL,
  `is_locked` enum('Y','N') NOT NULL DEFAULT 'N',
  `active_at` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
