CREATE TABLE `ss_user` (
  `user_id` int(11) NOT NULL,
  `port` int(11) NOT NULL,
  `password` varchar(32) NOT NULL,
  `flow_up` bigint(20) NOT NULL DEFAULT '0',
  `flow_down` bigint(20) NOT NULL DEFAULT '0',
  `transfer_enable` bigint(20) NOT NULL,
  `is_locked` enum('Y','N') NOT NULL DEFAULT 'N',
  `active_at` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `ss_transfer` (
  `transfer_id` int(11) NOT NULL,
  `user_id` varchar(32) NOT NULL,
  `node_id` int(11) NOT NULL,
  `flow_up` bigint(20) NOT NULL DEFAULT '0',
  `flow_down` bigint(20) NOT NULL DEFAULT '0',
  `active_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
