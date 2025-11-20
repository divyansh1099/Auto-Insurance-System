--
-- PostgreSQL database dump
--

\restrict vU0dT3p9D0HVMmrT8H50Vbfnta08BKuRXVKVBENladnm51MTOkXZGfQKp3nlRDi

-- Dumped from database version 15.14 (Debian 15.14-1.pgdg13+1)
-- Dumped by pg_dump version 15.14 (Debian 15.14-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: insurance_user
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO insurance_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: claims; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.claims (
    claim_id character varying(50) NOT NULL,
    driver_id character varying(50),
    policy_id character varying(50),
    claim_date date,
    claim_type character varying(50),
    claim_amount numeric(10,2),
    at_fault boolean,
    description text,
    status character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.claims OWNER TO insurance_user;

--
-- Name: devices; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.devices (
    device_id character varying(50) NOT NULL,
    driver_id character varying(50),
    vehicle_id character varying(50),
    device_type character varying(50),
    manufacturer character varying(100),
    firmware_version character varying(20),
    installed_date date,
    is_active boolean DEFAULT true,
    last_heartbeat timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.devices OWNER TO insurance_user;

--
-- Name: driver_statistics; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.driver_statistics (
    stat_id integer NOT NULL,
    driver_id character varying(50),
    period_start date,
    period_end date,
    total_miles numeric(10,2),
    total_trips integer,
    avg_speed numeric(6,2),
    max_speed numeric(6,2),
    harsh_braking_rate numeric(8,4),
    rapid_accel_rate numeric(8,4),
    speeding_rate numeric(8,4),
    night_driving_pct numeric(5,2),
    rush_hour_pct numeric(5,2),
    weekend_driving_pct numeric(5,2),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.driver_statistics OWNER TO insurance_user;

--
-- Name: driver_statistics_stat_id_seq; Type: SEQUENCE; Schema: public; Owner: insurance_user
--

CREATE SEQUENCE public.driver_statistics_stat_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.driver_statistics_stat_id_seq OWNER TO insurance_user;

--
-- Name: driver_statistics_stat_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: insurance_user
--

ALTER SEQUENCE public.driver_statistics_stat_id_seq OWNED BY public.driver_statistics.stat_id;


--
-- Name: drivers; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.drivers (
    driver_id character varying(50) NOT NULL,
    first_name character varying(100),
    last_name character varying(100),
    email character varying(255) NOT NULL,
    phone character varying(20),
    date_of_birth date,
    license_number character varying(50),
    license_state character varying(2),
    years_licensed integer,
    gender character varying(10),
    marital_status character varying(20),
    address text,
    city character varying(100),
    state character varying(2),
    zip_code character varying(10),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.drivers OWNER TO insurance_user;

--
-- Name: premiums; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.premiums (
    premium_id integer NOT NULL,
    driver_id character varying(50),
    policy_id character varying(50),
    base_premium numeric(10,2),
    risk_multiplier numeric(5,2),
    usage_multiplier numeric(5,2),
    discount_factor numeric(5,2),
    final_premium numeric(10,2),
    monthly_premium numeric(10,2),
    effective_date date,
    expiration_date date,
    status character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    policy_type character varying(20) DEFAULT 'PHYD'::character varying,
    coverage_type character varying(50) DEFAULT 'Comprehensive'::character varying,
    coverage_limit numeric(12,2) DEFAULT 100000.00,
    total_miles_allowed numeric(10,2),
    deductible numeric(10,2) DEFAULT 1000.00,
    policy_last_updated timestamp without time zone
);


ALTER TABLE public.premiums OWNER TO insurance_user;

--
-- Name: premiums_premium_id_seq; Type: SEQUENCE; Schema: public; Owner: insurance_user
--

CREATE SEQUENCE public.premiums_premium_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.premiums_premium_id_seq OWNER TO insurance_user;

--
-- Name: premiums_premium_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: insurance_user
--

ALTER SEQUENCE public.premiums_premium_id_seq OWNED BY public.premiums.premium_id;


--
-- Name: risk_scores; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.risk_scores (
    score_id integer NOT NULL,
    driver_id character varying(50),
    risk_score numeric(5,2),
    risk_category character varying(20),
    confidence numeric(5,2),
    model_version character varying(20),
    calculation_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    features jsonb,
    shap_values jsonb,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    behavior_score numeric(5,2),
    mileage_score numeric(5,2),
    time_pattern_score numeric(5,2),
    location_score numeric(5,2),
    speeding_frequency numeric(6,2) DEFAULT 0,
    acceleration_pattern numeric(6,2) DEFAULT 0,
    high_risk_area_exposure numeric(6,2) DEFAULT 0,
    weather_risk_exposure numeric(6,2) DEFAULT 0,
    hard_braking_frequency numeric(6,2) DEFAULT 0,
    night_driving_percentage numeric(6,2) DEFAULT 0,
    phone_usage_incidents integer DEFAULT 0,
    CONSTRAINT risk_scores_behavior_score_check CHECK (((behavior_score IS NULL) OR ((behavior_score >= (0)::numeric) AND (behavior_score <= (100)::numeric)))),
    CONSTRAINT risk_scores_location_score_check CHECK (((location_score IS NULL) OR ((location_score >= (0)::numeric) AND (location_score <= (100)::numeric)))),
    CONSTRAINT risk_scores_mileage_score_check CHECK (((mileage_score IS NULL) OR ((mileage_score >= (0)::numeric) AND (mileage_score <= (100)::numeric)))),
    CONSTRAINT risk_scores_risk_score_check CHECK (((risk_score >= (0)::numeric) AND (risk_score <= (100)::numeric))),
    CONSTRAINT risk_scores_time_pattern_score_check CHECK (((time_pattern_score IS NULL) OR ((time_pattern_score >= (0)::numeric) AND (time_pattern_score <= (100)::numeric))))
);


ALTER TABLE public.risk_scores OWNER TO insurance_user;

--
-- Name: risk_scores_score_id_seq; Type: SEQUENCE; Schema: public; Owner: insurance_user
--

CREATE SEQUENCE public.risk_scores_score_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.risk_scores_score_id_seq OWNER TO insurance_user;

--
-- Name: risk_scores_score_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: insurance_user
--

ALTER SEQUENCE public.risk_scores_score_id_seq OWNED BY public.risk_scores.score_id;


--
-- Name: telematics_events; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.telematics_events (
    event_id character varying(50) NOT NULL,
    device_id character varying(50),
    driver_id character varying(50),
    trip_id character varying(50),
    "timestamp" timestamp without time zone NOT NULL,
    latitude numeric(10,6),
    longitude numeric(10,6),
    speed numeric(6,2),
    acceleration numeric(6,3),
    braking_force numeric(6,3),
    heading numeric(6,2),
    altitude numeric(8,2),
    gps_accuracy numeric(6,2),
    event_type character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
)
PARTITION BY RANGE ("timestamp");


ALTER TABLE public.telematics_events OWNER TO insurance_user;

--
-- Name: telematics_events_2024_11; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.telematics_events_2024_11 (
    event_id character varying(50) NOT NULL,
    device_id character varying(50),
    driver_id character varying(50),
    trip_id character varying(50),
    "timestamp" timestamp without time zone NOT NULL,
    latitude numeric(10,6),
    longitude numeric(10,6),
    speed numeric(6,2),
    acceleration numeric(6,3),
    braking_force numeric(6,3),
    heading numeric(6,2),
    altitude numeric(8,2),
    gps_accuracy numeric(6,2),
    event_type character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.telematics_events_2024_11 OWNER TO insurance_user;

--
-- Name: telematics_events_2024_12; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.telematics_events_2024_12 (
    event_id character varying(50) NOT NULL,
    device_id character varying(50),
    driver_id character varying(50),
    trip_id character varying(50),
    "timestamp" timestamp without time zone NOT NULL,
    latitude numeric(10,6),
    longitude numeric(10,6),
    speed numeric(6,2),
    acceleration numeric(6,3),
    braking_force numeric(6,3),
    heading numeric(6,2),
    altitude numeric(8,2),
    gps_accuracy numeric(6,2),
    event_type character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.telematics_events_2024_12 OWNER TO insurance_user;

--
-- Name: telematics_events_2025_01; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.telematics_events_2025_01 (
    event_id character varying(50) NOT NULL,
    device_id character varying(50),
    driver_id character varying(50),
    trip_id character varying(50),
    "timestamp" timestamp without time zone NOT NULL,
    latitude numeric(10,6),
    longitude numeric(10,6),
    speed numeric(6,2),
    acceleration numeric(6,3),
    braking_force numeric(6,3),
    heading numeric(6,2),
    altitude numeric(8,2),
    gps_accuracy numeric(6,2),
    event_type character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.telematics_events_2025_01 OWNER TO insurance_user;

--
-- Name: telematics_events_2025_09; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.telematics_events_2025_09 (
    event_id character varying(50) NOT NULL,
    device_id character varying(50),
    driver_id character varying(50),
    trip_id character varying(50),
    "timestamp" timestamp without time zone NOT NULL,
    latitude numeric(10,6),
    longitude numeric(10,6),
    speed numeric(6,2),
    acceleration numeric(6,3),
    braking_force numeric(6,3),
    heading numeric(6,2),
    altitude numeric(8,2),
    gps_accuracy numeric(6,2),
    event_type character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.telematics_events_2025_09 OWNER TO insurance_user;

--
-- Name: telematics_events_2025_10; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.telematics_events_2025_10 (
    event_id character varying(50) NOT NULL,
    device_id character varying(50),
    driver_id character varying(50),
    trip_id character varying(50),
    "timestamp" timestamp without time zone NOT NULL,
    latitude numeric(10,6),
    longitude numeric(10,6),
    speed numeric(6,2),
    acceleration numeric(6,3),
    braking_force numeric(6,3),
    heading numeric(6,2),
    altitude numeric(8,2),
    gps_accuracy numeric(6,2),
    event_type character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.telematics_events_2025_10 OWNER TO insurance_user;

--
-- Name: trips; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.trips (
    trip_id character varying(50) NOT NULL,
    driver_id character varying(50),
    device_id character varying(50),
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone,
    duration_minutes numeric(10,2),
    distance_miles numeric(10,2),
    start_latitude numeric(10,6),
    start_longitude numeric(10,6),
    end_latitude numeric(10,6),
    end_longitude numeric(10,6),
    avg_speed numeric(6,2),
    max_speed numeric(6,2),
    harsh_braking_count integer DEFAULT 0,
    rapid_accel_count integer DEFAULT 0,
    speeding_count integer DEFAULT 0,
    harsh_corner_count integer DEFAULT 0,
    phone_usage_detected boolean DEFAULT false,
    trip_type character varying(20),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    origin_city character varying(100),
    origin_state character varying(50),
    destination_city character varying(100),
    destination_state character varying(50),
    trip_score integer,
    risk_level character varying(20),
    CONSTRAINT trips_risk_level_check CHECK (((risk_level IS NULL) OR ((risk_level)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying])::text[])))),
    CONSTRAINT trips_trip_score_check CHECK (((trip_score IS NULL) OR ((trip_score >= 0) AND (trip_score <= 100))))
);


ALTER TABLE public.trips OWNER TO insurance_user;

--
-- Name: users; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    driver_id character varying(50),
    username character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    hashed_password character varying(255) NOT NULL,
    is_active boolean DEFAULT true,
    is_admin boolean DEFAULT false,
    last_login timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.users OWNER TO insurance_user;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: insurance_user
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_user_id_seq OWNER TO insurance_user;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: insurance_user
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: vehicles; Type: TABLE; Schema: public; Owner: insurance_user
--

CREATE TABLE public.vehicles (
    vehicle_id character varying(50) NOT NULL,
    driver_id character varying(50),
    make character varying(50),
    model character varying(50),
    year integer,
    vin character varying(17),
    vehicle_type character varying(50),
    safety_rating integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT vehicles_safety_rating_check CHECK (((safety_rating >= 1) AND (safety_rating <= 5)))
);


ALTER TABLE public.vehicles OWNER TO insurance_user;

--
-- Name: telematics_events_2024_11; Type: TABLE ATTACH; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events ATTACH PARTITION public.telematics_events_2024_11 FOR VALUES FROM ('2024-11-01 00:00:00') TO ('2024-12-01 00:00:00');


--
-- Name: telematics_events_2024_12; Type: TABLE ATTACH; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events ATTACH PARTITION public.telematics_events_2024_12 FOR VALUES FROM ('2024-12-01 00:00:00') TO ('2025-01-01 00:00:00');


--
-- Name: telematics_events_2025_01; Type: TABLE ATTACH; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events ATTACH PARTITION public.telematics_events_2025_01 FOR VALUES FROM ('2025-01-01 00:00:00') TO ('2025-02-01 00:00:00');


--
-- Name: telematics_events_2025_09; Type: TABLE ATTACH; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events ATTACH PARTITION public.telematics_events_2025_09 FOR VALUES FROM ('2025-09-01 00:00:00') TO ('2025-10-01 00:00:00');


--
-- Name: telematics_events_2025_10; Type: TABLE ATTACH; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events ATTACH PARTITION public.telematics_events_2025_10 FOR VALUES FROM ('2025-10-01 00:00:00') TO ('2025-11-01 00:00:00');


--
-- Name: driver_statistics stat_id; Type: DEFAULT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.driver_statistics ALTER COLUMN stat_id SET DEFAULT nextval('public.driver_statistics_stat_id_seq'::regclass);


--
-- Name: premiums premium_id; Type: DEFAULT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.premiums ALTER COLUMN premium_id SET DEFAULT nextval('public.premiums_premium_id_seq'::regclass);


--
-- Name: risk_scores score_id; Type: DEFAULT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.risk_scores ALTER COLUMN score_id SET DEFAULT nextval('public.risk_scores_score_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Data for Name: claims; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.claims (claim_id, driver_id, policy_id, claim_date, claim_type, claim_amount, at_fault, description, status, created_at) FROM stdin;
\.


--
-- Data for Name: devices; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.devices (device_id, driver_id, vehicle_id, device_type, manufacturer, firmware_version, installed_date, is_active, last_heartbeat, created_at) FROM stdin;
DEV-0001	DRV-0001	VEH-0001	OBD-II	TelematicsCorp	v2.1	2025-06-13	t	2025-11-14 05:30:09.853799	2025-11-14 06:19:09.854576
DEV-0002	DRV-0002	VEH-0002	OBD-II	TelematicsCorp	v2.1	2025-08-16	t	\N	2025-11-14 06:20:27.981293
DEV-0003	DRV-0003	VEH-0003	OBD-II	TelematicsCorp	v2.1	2025-08-16	t	\N	2025-11-14 06:20:27.981294
DEV-0004	DRV-0004	VEH-0004	OBD-II	TelematicsCorp	v2.1	2025-08-16	t	\N	2025-11-14 06:20:27.981294
DEV-0005	DRV-0005	VEH-0005	OBD-II	TelematicsCorp	v2.1	2025-08-16	t	\N	2025-11-14 06:20:27.981294
DEV-0006	DRV-0006	VEH-0006	OBD-II	TelematicsCorp	v2.1	2025-08-16	t	\N	2025-11-14 06:20:27.981294
DEV-0007	DRV-0007	VEH-0007	OBD-II	TelematicsCorp	v2.1	2025-08-16	t	\N	2025-11-14 06:20:27.981295
\.


--
-- Data for Name: driver_statistics; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.driver_statistics (stat_id, driver_id, period_start, period_end, total_miles, total_trips, avg_speed, max_speed, harsh_braking_rate, rapid_accel_rate, speeding_rate, night_driving_pct, rush_hour_pct, weekend_driving_pct, created_at) FROM stdin;
\.


--
-- Data for Name: drivers; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.drivers (driver_id, first_name, last_name, email, phone, date_of_birth, license_number, license_state, years_licensed, gender, marital_status, address, city, state, zip_code, created_at, updated_at) FROM stdin;
DRV-0001	James	Smith	james.smith@example.com	555-8006	1980-10-26	DL14541098	CA	2	M	Married	194 Main St	Houston	CA	48176	2025-11-14 06:19:02.470671	2025-11-14 06:19:02.470673
DRV-0002	Mary	Johnson	mary.johnson@example.com	555-2980	1980-07-16	DL75878386	NY	19	F	Single	608 Main St	Houston	NY	62800	2025-11-14 06:19:02.470674	2025-11-14 06:19:02.470674
DRV-0003	John	Williams	john.williams@example.com	555-8460	1981-09-02	DL31972965	TX	13	F	Single	8508 Main St	Houston	TX	13293	2025-11-14 06:19:02.470674	2025-11-14 06:19:02.470675
DRV-0004	Patricia	Brown	patricia.brown@example.com	555-2855	1992-10-25	DL93273109	FL	12	F	Married	4026 Main St	Chicago	FL	22656	2025-11-14 06:19:02.470676	2025-11-14 06:19:02.470676
DRV-0005	Robert	Jones	robert.jones@example.com	555-7149	1996-06-15	DL55560110	IL	15	M	Married	860 Main St	Los Angeles	IL	92093	2025-11-14 06:19:02.470676	2025-11-14 06:19:02.470677
DRV-0006	Jennifer	Garcia	jennifer.garcia@example.com	555-7745	1988-11-24	DL66428736	AZ	10	M	Married	2783 Main St	Los Angeles	AZ	13420	2025-11-14 06:19:02.470677	2025-11-14 06:19:02.470677
DRV-0007	Michael	Miller	michael.miller@example.com	555-9138	1988-01-02	DL47628643	WA	24	F	Married	5583 Main St	Miami	WA	49726	2025-11-14 06:19:02.470677	2025-11-14 06:19:02.470677
DRV-0008	Linda	Davis	linda.davis@example.com	555-9130	2002-08-27	DL41496809	MA	13	M	Single	6335 Main St	Chicago	MA	94231	2025-11-14 06:19:02.470677	2025-11-14 06:19:02.470678
DRV-0009	William	Rodriguez	william.rodriguez@example.com	555-5145	2001-06-12	DL89031464	CO	15	F	Single	9337 Main St	Miami	CO	47270	2025-11-14 06:19:02.470678	2025-11-14 06:19:02.470678
DRV-0010	Elizabeth	Martinez	elizabeth.martinez@example.com	555-4956	2003-04-19	DL83890206	OR	26	F	Single	5913 Main St	Miami	OR	73951	2025-11-14 06:19:02.470678	2025-11-14 06:19:02.470678
\.


--
-- Data for Name: premiums; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.premiums (premium_id, driver_id, policy_id, base_premium, risk_multiplier, usage_multiplier, discount_factor, final_premium, monthly_premium, effective_date, expiration_date, status, created_at, updated_at, policy_type, coverage_type, coverage_limit, total_miles_allowed, deductible, policy_last_updated) FROM stdin;
1	DRV-0001	POL-0001	1000.00	0.70	0.91	0.97	615.20	51.27	2025-09-09	2026-09-24	active	2025-11-14 06:19:26.879527	2025-11-14 06:19:47.053356	PAYD	Liability	500000.00	8000.00	2000.00	2025-11-14 06:19:47.056065
2	DRV-0002	POL-0002	1400.00	1.14	1.06	0.96	1358.02	93.22	2025-10-15	2026-10-15	active	2025-11-14 06:20:27.97398	2025-11-14 06:20:27.973981	Hybrid	\N	\N	\N	\N	\N
3	DRV-0003	POL-0003	1000.00	1.19	0.92	0.95	1068.86	82.96	2025-10-15	2026-10-15	active	2025-11-14 06:20:27.973982	2025-11-14 06:20:27.973982	PHYD	\N	\N	\N	\N	\N
4	DRV-0004	POL-0004	1000.00	0.81	1.04	0.97	1372.04	113.73	2025-10-15	2026-10-15	active	2025-11-14 06:20:27.973982	2025-11-14 06:20:27.973984	PAYD	\N	\N	\N	\N	\N
5	DRV-0005	POL-0005	1400.00	0.87	1.01	0.99	1294.01	105.38	2025-10-15	2026-10-15	active	2025-11-14 06:20:27.973984	2025-11-14 06:20:27.973984	Hybrid	\N	\N	\N	\N	\N
6	DRV-0006	POL-0006	1000.00	0.88	1.00	0.95	1217.80	83.59	2025-10-15	2026-10-15	active	2025-11-14 06:20:27.973985	2025-11-14 06:20:27.973985	PAYD	\N	\N	\N	\N	\N
7	DRV-0007	POL-0007	1000.00	0.94	0.95	0.99	1058.58	88.88	2025-10-15	2026-10-15	active	2025-11-14 06:20:27.973985	2025-11-14 06:20:27.973985	PAYD	\N	\N	\N	\N	\N
\.


--
-- Data for Name: risk_scores; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.risk_scores (score_id, driver_id, risk_score, risk_category, confidence, model_version, calculation_date, features, shap_values, created_at, behavior_score, mileage_score, time_pattern_score, location_score, speeding_frequency, acceleration_pattern, high_risk_area_exposure, weather_risk_exposure, hard_braking_frequency, night_driving_percentage, phone_usage_incidents) FROM stdin;
2	DRV-0001	3.28	low	0.89	v2.0	2025-11-14 06:19:47.049745	{"total_miles": 2845.8, "total_trips": 40, "avg_trip_score": 96.72}	{"speeding_frequency": -1.27, "acceleration_pattern": -0.15, "hard_braking_frequency": -2.96}	2025-11-14 06:19:47.050781	90.55	72.01	75.73	66.03	0.28	0.70	20.56	21.74	0.21	20.00	1
3	DRV-0002	57.80	medium	0.89	v2.0	2025-11-14 06:20:26.787473	\N	\N	2025-11-14 06:20:27.978127	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	0
4	DRV-0003	36.61	medium	0.86	v2.0	2025-11-14 06:20:27.024297	\N	\N	2025-11-14 06:20:27.978128	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	0
5	DRV-0004	48.71	low	0.89	v2.0	2025-11-14 06:20:27.262614	\N	\N	2025-11-14 06:20:27.978129	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	0
6	DRV-0005	50.27	low	0.88	v2.0	2025-11-14 06:20:27.495397	\N	\N	2025-11-14 06:20:27.978129	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	0
7	DRV-0006	47.66	medium	0.89	v2.0	2025-11-14 06:20:27.73184	\N	\N	2025-11-14 06:20:27.978129	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	0
8	DRV-0007	32.07	low	0.95	v2.0	2025-11-14 06:20:27.970161	\N	\N	2025-11-14 06:20:27.978129	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	0
\.


--
-- Data for Name: telematics_events_2024_11; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.telematics_events_2024_11 (event_id, device_id, driver_id, trip_id, "timestamp", latitude, longitude, speed, acceleration, braking_force, heading, altitude, gps_accuracy, event_type, created_at) FROM stdin;
\.


--
-- Data for Name: telematics_events_2024_12; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.telematics_events_2024_12 (event_id, device_id, driver_id, trip_id, "timestamp", latitude, longitude, speed, acceleration, braking_force, heading, altitude, gps_accuracy, event_type, created_at) FROM stdin;
\.


--
-- Data for Name: telematics_events_2025_01; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.telematics_events_2025_01 (event_id, device_id, driver_id, trip_id, "timestamp", latitude, longitude, speed, acceleration, braking_force, heading, altitude, gps_accuracy, event_type, created_at) FROM stdin;
\.


--
-- Data for Name: telematics_events_2025_09; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.telematics_events_2025_09 (event_id, device_id, driver_id, trip_id, "timestamp", latitude, longitude, speed, acceleration, braking_force, heading, altitude, gps_accuracy, event_type, created_at) FROM stdin;
\.


--
-- Data for Name: telematics_events_2025_10; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.telematics_events_2025_10 (event_id, device_id, driver_id, trip_id, "timestamp", latitude, longitude, speed, acceleration, braking_force, heading, altitude, gps_accuracy, event_type, created_at) FROM stdin;
\.


--
-- Data for Name: trips; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.trips (trip_id, driver_id, device_id, start_time, end_time, duration_minutes, distance_miles, start_latitude, start_longitude, end_latitude, end_longitude, avg_speed, max_speed, harsh_braking_count, rapid_accel_count, speeding_count, harsh_corner_count, phone_usage_detected, trip_type, created_at, origin_city, origin_state, destination_city, destination_state, trip_score, risk_level) FROM stdin;
TRP-0001-0001	DRV-0001	DEV-0001	2025-09-17 15:59:26.849575	2025-09-17 17:57:32.086314	118.09	135.26	39.756407	-77.941216	36.136107	-111.990269	38.28	71.30	0	0	0	0	f	commute	2025-11-14 06:19:26.85273	Austin	TX	San Diego	CA	100	low
TRP-0001-0002	DRV-0001	DEV-0001	2025-11-06 18:21:26.849575	2025-11-06 19:22:14.235135	60.79	84.70	39.479893	-117.287419	34.504115	-76.680245	36.39	62.45	0	0	0	0	f	work	2025-11-14 06:19:26.852731	San Francisco	CA	Boston	MA	100	low
TRP-0001-0003	DRV-0001	DEV-0001	2025-09-26 19:45:26.849575	2025-09-26 20:40:20.247824	54.89	43.22	38.139275	-115.278510	38.456070	-120.481242	33.50	56.77	0	0	0	0	f	commute	2025-11-14 06:19:26.852731	Tampa	FL	Houston	TX	100	low
TRP-0001-0004	DRV-0001	DEV-0001	2025-10-02 20:14:26.849575	2025-10-02 21:42:31.697024	88.08	103.45	40.991657	-117.993453	44.393234	-105.643563	44.17	51.86	0	1	0	0	f	errand	2025-11-14 06:19:26.852731	Portland	OR	San Diego	CA	100	low
TRP-0001-0005	DRV-0001	DEV-0001	2025-09-15 16:22:26.849575	2025-09-15 17:56:18.523577	93.86	72.08	37.158167	-109.415385	41.493604	-103.231906	48.15	62.99	0	0	0	0	f	errand	2025-11-14 06:19:26.852733	Buffalo	NY	San Francisco	CA	100	low
TRP-0001-0006	DRV-0001	DEV-0001	2025-09-28 12:57:26.849575	2025-09-28 14:01:11.163788	63.74	47.82	38.010577	-88.753907	37.835453	-89.335299	49.50	77.40	0	4	0	2	f	errand	2025-11-14 06:19:26.852733	Albany	NY	New York	NY	82	low
TRP-0001-0007	DRV-0001	DEV-0001	2025-11-13 20:03:26.849575	2025-11-13 20:41:13.333455	37.77	23.50	35.552859	-90.755805	40.949522	-74.276985	58.51	56.44	0	0	0	0	t	errand	2025-11-14 06:19:26.852733	Houston	TX	Boston	MA	91	low
TRP-0001-0008	DRV-0001	DEV-0001	2025-10-02 08:41:26.849575	2025-10-02 10:09:57.700694	88.51	75.56	38.054719	-100.528597	40.702420	-75.546107	34.57	49.29	0	0	0	0	f	leisure	2025-11-14 06:19:26.852734	Chicago	IL	New York	NY	100	low
TRP-0001-0009	DRV-0001	DEV-0001	2025-11-09 13:27:26.849575	2025-11-09 14:16:50.460919	49.39	32.41	32.830913	-87.729785	32.187135	-95.503883	54.71	56.62	0	0	0	0	f	leisure	2025-11-14 06:19:26.852734	Portland	OR	Houston	TX	100	low
TRP-0001-0010	DRV-0001	DEV-0001	2025-09-28 09:01:26.849575	2025-09-28 10:26:47.269112	85.34	49.06	36.419046	-87.789341	36.606023	-114.184700	48.84	64.80	0	1	0	0	f	leisure	2025-11-14 06:19:26.852734	Boston	MA	Buffalo	NY	99	low
TRP-0001-0011	DRV-0001	DEV-0001	2025-11-05 13:29:26.849575	2025-11-05 14:47:58.968798	78.54	50.60	36.628126	-77.375702	43.601654	-102.874235	45.40	64.40	0	3	0	0	f	work	2025-11-14 06:19:26.852734	Portland	OR	Austin	TX	93	low
TRP-0001-0012	DRV-0001	DEV-0001	2025-09-22 22:42:26.849575	2025-09-22 23:44:25.098504	61.97	82.12	41.551772	-108.290008	44.101937	-93.847449	48.23	70.03	0	0	0	2	f	commute	2025-11-14 06:19:26.852734	Portland	OR	Albany	NY	96	low
TRP-0001-0013	DRV-0001	DEV-0001	2025-10-15 14:57:26.849575	2025-10-15 15:19:34.698726	22.13	11.76	37.296893	-83.535040	44.211339	-99.265308	45.59	45.88	0	0	1	0	f	leisure	2025-11-14 06:19:26.852735	Orlando	FL	Miami	FL	92	low
TRP-0001-0014	DRV-0001	DEV-0001	2025-09-19 00:08:26.849575	2025-09-19 00:58:38.534491	50.19	48.77	34.531726	-90.309102	32.417923	-84.107790	59.99	79.10	0	4	1	0	f	errand	2025-11-14 06:19:26.852735	Dallas	TX	Albany	NY	82	low
TRP-0001-0015	DRV-0001	DEV-0001	2025-09-26 22:34:26.849575	2025-09-27 00:28:03.366506	113.61	146.46	38.680388	-104.813511	44.449379	-93.769355	30.22	58.93	0	0	0	0	f	commute	2025-11-14 06:19:26.852735	Los Angeles	CA	Denver	CO	100	low
TRP-0001-0016	DRV-0001	DEV-0001	2025-10-26 14:41:26.849575	2025-10-26 16:34:04.929767	112.63	114.73	42.047323	-87.351958	32.626334	-95.548108	36.02	71.62	0	0	0	0	f	leisure	2025-11-14 06:19:26.852741	New York	NY	Seattle	WA	100	low
TRP-0001-0017	DRV-0001	DEV-0001	2025-10-22 17:20:26.849575	2025-10-22 19:12:52.8767	112.43	127.61	34.805345	-78.793820	40.693306	-82.498647	37.50	64.47	0	0	0	0	f	work	2025-11-14 06:19:26.852741	Chicago	IL	Houston	TX	100	low
TRP-0001-0018	DRV-0001	DEV-0001	2025-10-27 13:06:26.849575	2025-10-27 14:04:37.117766	58.17	43.83	43.277683	-119.339342	36.708367	-99.025823	54.04	68.25	2	0	0	0	f	errand	2025-11-14 06:19:26.852741	Boston	MA	Austin	TX	92	low
TRP-0001-0019	DRV-0001	DEV-0001	2025-09-30 21:34:26.849575	2025-09-30 22:41:28.163926	67.02	56.04	35.448844	-80.079272	37.092775	-97.525368	55.95	60.76	0	3	0	0	f	work	2025-11-14 06:19:26.852742	Los Angeles	CA	Boston	MA	93	low
TRP-0001-0020	DRV-0001	DEV-0001	2025-09-26 16:44:26.849575	2025-09-26 18:09:14.124796	84.79	123.31	44.939022	-83.831884	32.056173	-105.278562	47.75	49.04	0	0	0	0	f	errand	2025-11-14 06:19:26.852742	Los Angeles	CA	Dallas	TX	100	low
TRP-0001-0021	DRV-0001	DEV-0001	2025-10-22 20:43:26.849575	2025-10-22 21:07:38.685977	24.20	23.94	32.895614	-113.811403	41.839425	-121.842551	27.73	61.00	0	0	1	0	f	work	2025-11-14 06:19:26.852742	Albany	NY	San Diego	CA	93	low
TRP-0001-0022	DRV-0001	DEV-0001	2025-10-10 21:22:26.849575	2025-10-10 23:06:40.091608	104.22	148.69	36.173539	-88.227945	34.991320	-89.709818	35.01	47.30	0	0	1	0	f	errand	2025-11-14 06:19:26.852742	Dallas	TX	Seattle	WA	97	low
TRP-0001-0023	DRV-0001	DEV-0001	2025-09-14 07:28:26.849575	2025-09-14 08:28:13.124882	59.77	59.16	36.901139	-81.855254	38.899885	-80.169946	36.22	69.18	1	0	0	0	f	leisure	2025-11-14 06:19:26.852742	New York	NY	Miami	FL	97	low
TRP-0001-0024	DRV-0001	DEV-0001	2025-11-11 11:04:26.849575	2025-11-11 12:33:56.203287	89.49	91.98	34.961211	-112.756232	44.707038	-107.519192	30.27	65.50	0	4	0	0	f	commute	2025-11-14 06:19:26.852743	Houston	TX	Denver	CO	92	low
TRP-0001-0025	DRV-0001	DEV-0001	2025-10-14 15:05:26.849575	2025-10-14 15:35:32.488672	30.09	37.65	34.685301	-75.398821	42.404067	-116.666553	40.92	78.70	0	0	0	0	f	commute	2025-11-14 06:19:26.852743	Miami	FL	Dallas	TX	100	low
TRP-0001-0026	DRV-0001	DEV-0001	2025-11-06 17:54:26.849575	2025-11-06 19:00:37.610071	66.18	45.75	33.175762	-110.586584	43.853429	-115.458824	43.80	46.01	0	0	0	0	f	leisure	2025-11-14 06:19:26.852743	Phoenix	AZ	San Francisco	CA	100	low
TRP-0001-0027	DRV-0001	DEV-0001	2025-11-04 11:57:26.849575	2025-11-04 12:37:44.617671	40.30	57.26	39.771730	-90.263004	35.798884	-118.247140	47.41	63.87	0	0	0	1	f	commute	2025-11-14 06:19:26.852743	Dallas	TX	Orlando	FL	98	low
TRP-0001-0028	DRV-0001	DEV-0001	2025-09-15 00:09:26.849575	2025-09-15 01:30:26.337017	80.99	105.51	36.262262	-107.297886	41.558268	-85.348843	30.54	61.61	0	0	1	0	f	commute	2025-11-14 06:19:26.852743	Houston	TX	Dallas	TX	97	low
TRP-0001-0029	DRV-0001	DEV-0001	2025-10-02 23:14:26.849575	2025-10-03 00:25:44.812335	71.30	45.69	36.174667	-117.544037	39.175409	-90.364005	28.36	70.38	0	0	0	1	f	errand	2025-11-14 06:19:26.852744	Houston	TX	Miami	FL	98	low
TRP-0001-0030	DRV-0001	DEV-0001	2025-09-27 22:48:26.849575	2025-09-27 23:09:04.751349	20.63	11.67	36.980154	-90.695504	42.216832	-76.285269	30.83	68.38	2	0	0	0	f	commute	2025-11-14 06:19:26.852744	Los Angeles	CA	Dallas	TX	90	low
TRP-0001-0031	DRV-0001	DEV-0001	2025-10-03 16:00:26.849575	2025-10-03 17:53:16.371907	112.83	116.81	36.131395	-116.630778	33.599780	-80.468320	43.52	63.42	0	0	1	0	f	work	2025-11-14 06:19:26.852744	Los Angeles	CA	Denver	CO	97	low
TRP-0001-0032	DRV-0001	DEV-0001	2025-10-01 19:59:26.849575	2025-10-01 20:20:12.964513	20.77	21.68	32.543020	-115.402805	33.776375	-89.200027	45.98	59.60	0	0	0	0	f	work	2025-11-14 06:19:26.852744	Phoenix	AZ	Albany	NY	100	low
TRP-0001-0033	DRV-0001	DEV-0001	2025-10-11 08:51:26.849575	2025-10-11 09:54:54.653377	63.46	41.73	42.923051	-121.355918	38.598644	-111.456821	42.43	46.15	0	0	0	0	f	work	2025-11-14 06:19:26.852744	Portland	OR	Buffalo	NY	100	low
TRP-0001-0034	DRV-0001	DEV-0001	2025-09-25 23:14:26.849575	2025-09-26 01:02:23.45866	107.94	87.74	36.611248	-116.812302	37.503708	-83.389033	32.51	55.79	1	0	0	0	f	errand	2025-11-14 06:19:26.852745	Tampa	FL	Buffalo	NY	99	low
TRP-0001-0035	DRV-0001	DEV-0001	2025-10-19 09:56:26.849575	2025-10-19 11:29:32.423859	93.09	72.59	41.482135	-86.213215	41.617775	-111.527719	25.39	74.85	0	0	1	0	f	errand	2025-11-14 06:19:26.852745	Tampa	FL	Miami	FL	95	low
TRP-0001-0036	DRV-0001	DEV-0001	2025-09-14 13:56:26.849575	2025-09-14 15:14:05.847091	77.65	75.81	40.920576	-111.872236	34.057472	-87.265104	34.10	71.02	0	0	0	0	f	commute	2025-11-14 06:19:26.852745	Portland	OR	Dallas	TX	100	low
TRP-0001-0037	DRV-0001	DEV-0001	2025-10-29 11:09:26.849575	2025-10-29 11:46:24.392672	36.96	39.33	36.590172	-121.709266	40.951300	-105.069378	58.52	48.68	0	0	0	0	f	errand	2025-11-14 06:19:26.852745	Phoenix	AZ	Dallas	TX	100	low
TRP-0001-0038	DRV-0001	DEV-0001	2025-10-25 19:15:26.849575	2025-10-25 19:47:28.36158	32.03	45.73	39.604218	-91.283747	33.019734	-106.646480	37.71	66.50	0	0	0	0	f	leisure	2025-11-14 06:19:26.852745	Albany	NY	Chicago	IL	100	low
TRP-0001-0039	DRV-0001	DEV-0001	2025-10-10 00:17:26.849575	2025-10-10 02:09:50.036316	112.39	145.08	38.826517	-98.137212	34.515386	-83.992746	32.33	50.43	0	0	0	0	f	errand	2025-11-14 06:19:26.852745	Miami	FL	Phoenix	AZ	100	low
TRP-0001-0040	DRV-0001	DEV-0001	2025-10-16 11:48:26.849575	2025-10-16 13:03:07.889076	74.68	99.71	36.311101	-118.509498	40.549355	-87.382309	52.27	46.54	0	0	1	0	f	commute	2025-11-14 06:19:26.852746	Chicago	IL	Buffalo	NY	96	low
TRP-0002-0001	DRV-0002	DEV-0002	2025-10-14 13:08:26.785485	2025-10-14 14:26:17.647975	77.85	71.72	37.389473	-99.343344	40.796054	-99.865642	30.17	73.42	2	1	1	0	f	commute	2025-11-14 06:20:27.984448	New York	TX	Tampa	CA	91	low
TRP-0002-0002	DRV-0002	DEV-0002	2025-11-05 21:18:26.785485	2025-11-05 22:36:36.628582	78.16	42.64	33.397975	-114.430836	34.714588	-75.159859	41.96	74.18	0	1	0	1	t	errand	2025-11-14 06:20:27.984449	Los Angeles	TX	San Francisco	FL	78	low
TRP-0002-0003	DRV-0002	DEV-0002	2025-11-10 23:56:26.785485	2025-11-11 01:17:54.023112	81.45	45.43	43.678003	-79.983164	32.578175	-77.157279	35.12	62.25	1	2	1	0	f	commute	2025-11-14 06:20:27.98445	Houston	NY	Buffalo	CA	88	low
TRP-0002-0004	DRV-0002	DEV-0002	2025-10-30 16:26:26.785485	2025-10-30 16:45:41.683318	19.25	11.62	37.962507	-87.978823	38.824063	-91.507491	26.25	60.06	1	3	0	2	f	commute	2025-11-14 06:20:27.98445	Houston	TX	Tampa	FL	83	medium
TRP-0002-0005	DRV-0002	DEV-0002	2025-10-24 14:27:26.785485	2025-10-24 15:52:22.20367	84.92	45.37	36.358301	-95.165012	44.715181	-87.319357	34.49	61.77	0	1	1	0	f	errand	2025-11-14 06:20:27.98445	Miami	CA	Buffalo	NY	71	low
TRP-0002-0006	DRV-0002	DEV-0002	2025-11-10 08:59:26.785485	2025-11-10 09:35:08.743718	35.70	38.34	36.340042	-92.778463	35.250461	-87.826797	30.20	56.74	0	2	0	1	f	commute	2025-11-14 06:20:27.98445	Houston	NY	San Francisco	NY	75	low
TRP-0002-0007	DRV-0002	DEV-0002	2025-10-27 07:30:26.785485	2025-10-27 07:55:13.465908	24.78	19.18	41.085172	-118.592134	39.825696	-93.304961	51.29	59.57	0	2	1	2	f	commute	2025-11-14 06:20:27.984451	Miami	FL	Tampa	TX	85	medium
TRP-0002-0008	DRV-0002	DEV-0002	2025-10-17 22:51:26.785485	2025-10-17 23:13:32.464262	22.09	15.70	37.763605	-80.450470	34.629666	-104.964179	40.86	60.37	1	3	0	2	t	commute	2025-11-14 06:20:27.984451	Los Angeles	TX	Buffalo	NY	72	low
TRP-0002-0009	DRV-0002	DEV-0002	2025-10-16 12:37:26.785485	2025-10-16 13:53:08.383487	75.69	90.65	40.722814	-106.242851	44.160801	-107.428907	41.85	67.66	0	1	1	0	t	errand	2025-11-14 06:20:27.984451	New York	FL	Tampa	FL	81	medium
TRP-0002-0010	DRV-0002	DEV-0002	2025-11-10 12:16:26.785485	2025-11-10 13:21:54.973023	65.47	32.97	37.627674	-82.702550	40.139070	-89.533844	37.53	71.24	1	0	1	1	f	leisure	2025-11-14 06:20:27.984451	Houston	FL	Buffalo	CA	88	medium
TRP-0002-0011	DRV-0002	DEV-0002	2025-11-05 11:27:26.785485	2025-11-05 12:45:45.373545	78.31	74.90	38.458268	-76.415117	34.341894	-101.279407	47.96	59.42	2	2	1	0	f	leisure	2025-11-14 06:20:27.984452	Los Angeles	FL	Tampa	TX	95	low
TRP-0002-0012	DRV-0002	DEV-0002	2025-11-01 16:50:26.785485	2025-11-01 18:14:53.266455	84.44	71.46	42.913709	-84.660688	36.248630	-116.428803	34.76	45.98	1	2	0	0	f	commute	2025-11-14 06:20:27.984452	New York	CA	Tampa	FL	87	medium
TRP-0002-0013	DRV-0002	DEV-0002	2025-10-27 10:17:26.785485	2025-10-27 10:56:18.991497	38.87	25.30	43.794607	-87.517354	34.174254	-102.121850	29.20	72.67	1	2	1	0	f	commute	2025-11-14 06:20:27.984452	Miami	CA	Tampa	CA	76	medium
TRP-0002-0014	DRV-0002	DEV-0002	2025-11-12 16:50:26.785485	2025-11-12 17:33:12.516762	42.76	36.55	40.164310	-95.125644	41.589065	-106.923470	39.07	53.37	1	1	1	1	f	commute	2025-11-14 06:20:27.984452	Houston	NY	Buffalo	NY	86	low
TRP-0002-0015	DRV-0002	DEV-0002	2025-10-28 18:34:26.785485	2025-10-28 19:43:07.347842	68.68	57.16	37.562882	-77.813284	39.297815	-117.248535	37.88	65.35	1	0	1	1	f	errand	2025-11-14 06:20:27.984453	New York	CA	Dallas	NY	90	low
TRP-0002-0016	DRV-0002	DEV-0002	2025-11-01 10:16:26.785485	2025-11-01 10:57:55.988465	41.49	39.81	43.575901	-90.497267	42.932413	-91.805056	38.68	71.70	0	1	0	2	f	errand	2025-11-14 06:20:27.984453	Los Angeles	CA	San Francisco	FL	70	low
TRP-0002-0017	DRV-0002	DEV-0002	2025-11-03 00:11:26.785485	2025-11-03 01:29:08.028499	77.69	52.47	33.355121	-74.486348	37.427006	-101.790652	29.27	71.91	1	2	0	1	f	commute	2025-11-14 06:20:27.984453	Miami	TX	San Francisco	NY	75	low
TRP-0002-0018	DRV-0002	DEV-0002	2025-10-27 08:41:26.785485	2025-10-27 08:56:42.086744	15.26	12.29	37.902533	-118.974234	36.375891	-83.749834	32.50	74.91	1	2	0	2	f	commute	2025-11-14 06:20:27.984453	New York	NY	Tampa	NY	74	low
TRP-0002-0019	DRV-0002	DEV-0002	2025-10-24 13:01:26.785485	2025-10-24 13:39:25.584255	37.98	30.66	37.695098	-99.266894	41.580971	-104.508546	29.78	66.20	2	3	0	0	f	errand	2025-11-14 06:20:27.984453	Los Angeles	NY	Dallas	TX	95	medium
TRP-0002-0020	DRV-0002	DEV-0002	2025-11-05 12:03:26.785485	2025-11-05 12:53:04.612804	49.63	25.04	33.681657	-104.812570	41.168509	-79.480901	47.11	49.58	2	0	0	1	f	commute	2025-11-14 06:20:27.984454	New York	CA	Dallas	FL	92	low
TRP-0002-0021	DRV-0002	DEV-0002	2025-10-16 00:10:26.785485	2025-10-16 00:55:43.926302	45.29	38.75	41.300066	-89.113232	43.285866	-93.592566	31.04	58.26	1	2	0	1	f	leisure	2025-11-14 06:20:27.984454	New York	TX	Tampa	TX	72	low
TRP-0002-0022	DRV-0002	DEV-0002	2025-10-24 11:16:26.785485	2025-10-24 11:52:12.200278	35.76	29.94	42.720574	-114.203094	39.078389	-112.501353	27.69	46.99	2	3	0	1	t	errand	2025-11-14 06:20:27.984454	Houston	CA	Buffalo	TX	82	low
TRP-0002-0023	DRV-0002	DEV-0002	2025-10-26 07:35:26.785485	2025-10-26 08:57:13.130614	81.77	76.26	32.742000	-108.987670	35.457758	-90.768529	37.09	61.52	0	1	1	2	f	leisure	2025-11-14 06:20:27.984454	New York	TX	Buffalo	NY	85	medium
TRP-0002-0024	DRV-0002	DEV-0002	2025-10-19 09:03:26.785485	2025-10-19 09:56:40.714197	53.23	53.36	42.881463	-103.212320	41.201992	-85.906810	38.84	66.73	0	3	1	1	f	leisure	2025-11-14 06:20:27.984454	New York	CA	Tampa	FL	88	low
TRP-0002-0025	DRV-0002	DEV-0002	2025-11-10 13:22:26.785485	2025-11-10 13:44:46.38818	22.33	21.14	43.968098	-79.125069	33.614058	-119.857647	30.12	73.83	2	2	0	2	f	leisure	2025-11-14 06:20:27.984455	New York	TX	San Francisco	CA	95	medium
TRP-0002-0026	DRV-0002	DEV-0002	2025-11-07 15:20:26.785485	2025-11-07 16:49:09.950186	88.72	63.25	43.337179	-79.762729	33.222195	-106.912463	27.37	70.12	1	3	0	0	f	errand	2025-11-14 06:20:27.984455	Miami	CA	Buffalo	FL	73	low
TRP-0002-0027	DRV-0002	DEV-0002	2025-11-01 20:08:26.785485	2025-11-01 20:49:41.218462	41.24	42.02	33.455104	-102.861280	40.781383	-77.307294	36.28	49.69	0	0	1	0	f	commute	2025-11-14 06:20:27.984455	Los Angeles	CA	Dallas	CA	93	medium
TRP-0002-0028	DRV-0002	DEV-0002	2025-10-26 18:19:26.785485	2025-10-26 19:08:30.596626	49.06	29.06	43.148115	-114.044413	38.443561	-116.361623	29.98	67.85	0	0	0	1	f	errand	2025-11-14 06:20:27.984455	Miami	NY	San Francisco	NY	86	low
TRP-0002-0029	DRV-0002	DEV-0002	2025-11-08 13:25:26.785485	2025-11-08 13:48:01.540681	22.58	19.77	43.309624	-120.435964	36.390082	-100.733969	52.27	70.24	1	0	0	2	f	errand	2025-11-14 06:20:27.984455	New York	CA	San Francisco	TX	88	low
TRP-0002-0030	DRV-0002	DEV-0002	2025-10-31 22:03:26.785485	2025-10-31 22:29:55.786803	26.48	29.99	33.328399	-105.782782	39.311698	-110.217490	28.79	71.71	0	0	1	2	f	leisure	2025-11-14 06:20:27.984456	Los Angeles	CA	San Francisco	CA	91	medium
TRP-0003-0001	DRV-0003	DEV-0003	2025-10-21 10:46:27.022866	2025-10-21 12:07:18.126012	80.85	69.33	41.148569	-99.757591	41.296281	-82.742533	46.38	60.30	2	2	1	0	f	commute	2025-11-14 06:20:27.984456	Miami	CA	San Francisco	FL	76	medium
TRP-0003-0002	DRV-0003	DEV-0003	2025-11-02 15:25:27.022866	2025-11-02 16:09:50.815551	44.40	22.93	34.012734	-76.771549	36.963417	-120.240722	38.03	65.66	0	1	1	2	f	leisure	2025-11-14 06:20:27.984456	Los Angeles	CA	Tampa	TX	76	medium
TRP-0003-0003	DRV-0003	DEV-0003	2025-11-11 17:01:27.022866	2025-11-11 18:07:09.850138	65.71	49.45	42.746221	-109.065340	34.591447	-97.306773	35.99	64.56	0	2	1	1	t	errand	2025-11-14 06:20:27.984456	Miami	NY	Tampa	FL	74	low
TRP-0003-0004	DRV-0003	DEV-0003	2025-10-17 09:37:27.022866	2025-10-17 10:27:05.599937	49.64	30.03	38.521789	-78.092175	37.142531	-109.808371	39.53	64.14	1	3	1	2	f	errand	2025-11-14 06:20:27.984457	Houston	CA	Tampa	FL	86	medium
TRP-0003-0005	DRV-0003	DEV-0003	2025-10-27 08:36:27.022866	2025-10-27 09:47:15.303714	70.80	47.35	35.626893	-108.843292	42.343378	-117.242171	50.97	55.24	0	2	0	1	f	leisure	2025-11-14 06:20:27.984457	Houston	NY	Tampa	CA	81	low
TRP-0003-0006	DRV-0003	DEV-0003	2025-10-29 00:08:27.022866	2025-10-29 01:02:17.777616	53.85	48.91	38.625893	-102.655075	36.054796	-102.472615	47.62	68.39	1	3	1	0	f	commute	2025-11-14 06:20:27.984457	New York	CA	San Francisco	FL	95	low
TRP-0003-0007	DRV-0003	DEV-0003	2025-11-13 18:39:27.022866	2025-11-13 19:37:07.483246	57.67	43.30	36.456701	-88.034907	43.906883	-103.830909	45.84	69.46	0	3	1	2	f	commute	2025-11-14 06:20:27.984457	Miami	FL	Buffalo	NY	86	low
TRP-0003-0008	DRV-0003	DEV-0003	2025-10-27 09:39:27.022866	2025-10-27 10:48:11.99505	68.75	82.43	39.965368	-93.238418	41.431394	-110.318402	33.74	69.66	1	3	1	0	f	commute	2025-11-14 06:20:27.984457	New York	TX	San Francisco	TX	85	low
TRP-0003-0009	DRV-0003	DEV-0003	2025-10-28 11:10:27.022866	2025-10-28 11:48:14.450113	37.79	32.34	41.679755	-82.853512	34.032138	-119.755060	27.36	52.96	1	2	0	2	f	leisure	2025-11-14 06:20:27.984458	New York	CA	San Francisco	NY	82	medium
TRP-0003-0010	DRV-0003	DEV-0003	2025-10-16 15:45:27.022866	2025-10-16 17:11:53.376803	86.44	46.35	44.605116	-96.785053	38.009281	-111.810493	50.20	58.69	1	2	1	1	f	commute	2025-11-14 06:20:27.984458	New York	FL	San Francisco	NY	85	medium
TRP-0003-0011	DRV-0003	DEV-0003	2025-10-15 18:30:27.022866	2025-10-15 19:43:35.074733	73.13	82.62	32.226448	-90.900536	40.904164	-74.916966	49.93	59.29	2	0	1	2	f	errand	2025-11-14 06:20:27.984458	Houston	CA	Dallas	CA	85	low
TRP-0003-0012	DRV-0003	DEV-0003	2025-10-19 08:34:27.022866	2025-10-19 08:57:21.645484	22.91	12.35	40.447165	-77.072176	37.083173	-95.643656	27.32	52.40	2	1	0	0	f	errand	2025-11-14 06:20:27.984458	Houston	FL	San Francisco	CA	78	low
TRP-0003-0013	DRV-0003	DEV-0003	2025-11-11 22:31:27.022866	2025-11-11 23:32:31.149787	61.07	61.56	35.322008	-102.321404	40.498691	-79.307055	41.71	45.73	1	3	1	2	f	commute	2025-11-14 06:20:27.984458	Los Angeles	CA	Dallas	TX	70	low
TRP-0003-0014	DRV-0003	DEV-0003	2025-11-04 19:45:27.022866	2025-11-04 20:24:51.084358	39.40	19.92	42.484973	-109.357885	38.500898	-106.378581	29.13	66.25	0	3	1	1	f	errand	2025-11-14 06:20:27.984459	New York	CA	San Francisco	TX	86	low
TRP-0003-0015	DRV-0003	DEV-0003	2025-10-14 18:35:27.022866	2025-10-14 18:54:15.813491	18.81	22.45	37.372724	-81.339917	33.945914	-109.758436	37.00	46.50	0	0	0	1	t	leisure	2025-11-14 06:20:27.984459	Los Angeles	NY	Dallas	TX	84	medium
TRP-0003-0016	DRV-0003	DEV-0003	2025-10-18 11:00:27.022866	2025-10-18 12:09:28.277551	69.02	74.06	36.058063	-111.244491	43.386004	-99.941313	44.69	49.00	0	1	1	2	f	leisure	2025-11-14 06:20:27.984459	Los Angeles	TX	Dallas	FL	75	medium
TRP-0003-0017	DRV-0003	DEV-0003	2025-10-20 09:16:27.022866	2025-10-20 10:20:33.923688	64.12	39.34	36.932832	-75.457131	34.256145	-78.385259	41.96	72.50	1	1	0	2	f	leisure	2025-11-14 06:20:27.984459	Miami	NY	Buffalo	FL	95	medium
TRP-0003-0018	DRV-0003	DEV-0003	2025-10-29 14:51:27.022866	2025-10-29 15:35:31.969395	44.08	22.89	36.491705	-99.297705	36.038063	-74.922679	27.74	49.28	1	2	1	1	f	leisure	2025-11-14 06:20:27.98446	Los Angeles	NY	San Francisco	FL	72	medium
TRP-0003-0019	DRV-0003	DEV-0003	2025-10-29 20:03:27.022866	2025-10-29 21:10:36.942568	67.17	77.27	35.962805	-118.952369	39.836051	-101.889319	33.85	57.95	0	3	1	2	f	leisure	2025-11-14 06:20:27.98446	Los Angeles	FL	San Francisco	NY	88	medium
TRP-0003-0020	DRV-0003	DEV-0003	2025-11-11 00:14:27.022866	2025-11-11 01:01:25.549477	46.98	38.27	40.738947	-87.733416	33.677046	-83.767246	42.13	57.55	2	3	0	1	f	errand	2025-11-14 06:20:27.98446	Houston	TX	San Francisco	TX	78	medium
TRP-0003-0021	DRV-0003	DEV-0003	2025-10-16 22:15:27.022866	2025-10-16 23:21:34.548965	66.13	52.16	44.394295	-118.916461	38.399640	-94.734496	41.90	57.59	0	3	0	1	f	errand	2025-11-14 06:20:27.98446	Houston	CA	Tampa	NY	95	low
TRP-0003-0022	DRV-0003	DEV-0003	2025-10-20 12:46:27.022866	2025-10-20 13:14:22.40416	27.92	17.82	37.631397	-113.852030	32.792906	-91.558187	39.45	46.02	0	0	0	0	f	leisure	2025-11-14 06:20:27.984461	Houston	TX	Tampa	FL	87	low
TRP-0003-0023	DRV-0003	DEV-0003	2025-11-10 12:04:27.022866	2025-11-10 12:42:16.02565	37.82	37.87	33.732500	-77.378407	34.428877	-81.961187	51.75	61.53	1	0	0	0	f	leisure	2025-11-14 06:20:27.984461	Miami	TX	Buffalo	TX	90	low
TRP-0003-0024	DRV-0003	DEV-0003	2025-10-21 08:54:27.022866	2025-10-21 09:12:33.107143	18.10	14.82	42.169185	-89.403815	42.161214	-79.213129	43.05	50.85	0	3	1	1	f	commute	2025-11-14 06:20:27.984462	Houston	TX	Dallas	TX	76	medium
TRP-0003-0025	DRV-0003	DEV-0003	2025-10-31 20:50:27.022866	2025-10-31 21:51:57.866111	61.51	62.04	40.428913	-107.842408	37.824812	-113.446474	37.38	46.28	1	2	1	0	t	errand	2025-11-14 06:20:27.984462	Houston	TX	Buffalo	TX	86	medium
TRP-0003-0026	DRV-0003	DEV-0003	2025-11-05 16:08:27.022866	2025-11-05 17:31:30.843384	83.06	71.13	32.583598	-82.583649	34.375788	-88.982091	27.36	68.15	1	0	1	1	f	leisure	2025-11-14 06:20:27.984462	New York	NY	Buffalo	TX	84	medium
TRP-0003-0027	DRV-0003	DEV-0003	2025-10-17 18:05:27.022866	2025-10-17 19:04:24.878604	58.96	59.99	44.190531	-80.008118	42.328849	-108.453892	54.95	74.63	1	3	1	2	f	leisure	2025-11-14 06:20:27.984462	New York	FL	Tampa	TX	87	medium
TRP-0003-0028	DRV-0003	DEV-0003	2025-10-29 19:27:27.022866	2025-10-29 19:46:05.276699	18.64	16.18	40.158008	-75.787649	44.748610	-101.384220	27.18	64.06	0	0	1	0	f	commute	2025-11-14 06:20:27.984462	Houston	FL	Tampa	CA	73	medium
TRP-0003-0029	DRV-0003	DEV-0003	2025-11-04 09:28:27.022866	2025-11-04 10:51:30.468758	83.06	58.80	35.493707	-117.389767	42.375829	-86.621991	45.73	70.70	1	0	1	1	f	errand	2025-11-14 06:20:27.984463	Los Angeles	TX	Dallas	FL	89	low
TRP-0003-0030	DRV-0003	DEV-0003	2025-11-05 19:59:27.022866	2025-11-05 20:30:38.349334	31.19	28.50	32.259287	-116.972587	35.725191	-89.393062	38.57	73.17	2	3	0	0	f	commute	2025-11-14 06:20:27.984463	New York	NY	San Francisco	CA	75	low
TRP-0004-0001	DRV-0004	DEV-0004	2025-10-21 18:34:27.261301	2025-10-21 19:10:25.623796	35.97	24.75	35.409601	-79.740916	36.631364	-90.273567	39.86	65.97	0	0	0	0	f	errand	2025-11-14 06:20:27.984463	Los Angeles	TX	Buffalo	NY	70	low
TRP-0004-0002	DRV-0004	DEV-0004	2025-11-11 08:44:27.261301	2025-11-11 10:09:08.238753	84.68	69.11	44.672269	-81.983897	38.184425	-88.780602	44.44	49.73	0	1	1	1	f	commute	2025-11-14 06:20:27.984463	Miami	FL	San Francisco	FL	81	low
TRP-0004-0003	DRV-0004	DEV-0004	2025-10-15 16:01:27.261301	2025-10-15 17:29:23.335419	87.93	66.63	35.553825	-98.332764	41.730958	-91.143131	30.62	48.15	1	2	0	1	f	commute	2025-11-14 06:20:27.984463	Miami	TX	San Francisco	TX	76	low
TRP-0004-0004	DRV-0004	DEV-0004	2025-10-16 18:38:27.261301	2025-10-16 18:55:48.902252	17.36	9.39	40.144411	-86.342261	38.785536	-93.497070	41.71	54.37	0	3	0	0	t	leisure	2025-11-14 06:20:27.984464	New York	FL	San Francisco	TX	88	medium
TRP-0004-0005	DRV-0004	DEV-0004	2025-11-11 17:43:27.261301	2025-11-11 18:29:51.300584	46.40	42.02	33.718595	-108.451028	33.441533	-79.530002	39.64	60.11	2	0	0	0	t	errand	2025-11-14 06:20:27.984464	Miami	TX	Buffalo	NY	81	medium
TRP-0004-0006	DRV-0004	DEV-0004	2025-10-30 07:28:27.261301	2025-10-30 08:41:29.720838	73.04	63.84	38.634188	-96.522439	32.688274	-86.817031	40.98	68.54	1	2	0	2	f	leisure	2025-11-14 06:20:27.984464	Houston	TX	Tampa	FL	86	medium
TRP-0004-0007	DRV-0004	DEV-0004	2025-11-02 21:44:27.261301	2025-11-02 22:10:17.837482	25.84	28.84	32.617289	-79.523987	44.100656	-109.189456	43.97	74.95	2	3	0	0	f	commute	2025-11-14 06:20:27.984464	Los Angeles	NY	San Francisco	FL	71	medium
TRP-0004-0008	DRV-0004	DEV-0004	2025-10-26 08:27:27.261301	2025-10-26 09:55:18.690674	87.86	84.90	34.867605	-117.131710	32.661650	-85.159607	34.84	58.62	0	2	1	1	f	errand	2025-11-14 06:20:27.984465	Miami	NY	San Francisco	FL	79	low
TRP-0004-0009	DRV-0004	DEV-0004	2025-10-31 18:04:27.261301	2025-10-31 18:57:13.22828	52.77	61.98	43.491244	-92.060794	39.246160	-75.950948	51.27	46.64	2	0	0	1	t	leisure	2025-11-14 06:20:27.984465	New York	NY	Tampa	TX	91	medium
TRP-0004-0010	DRV-0004	DEV-0004	2025-10-28 14:10:27.261301	2025-10-28 14:52:12.16829	41.75	34.61	36.891337	-94.065039	34.445578	-120.897098	49.26	64.13	0	2	1	2	f	leisure	2025-11-14 06:20:27.984465	Miami	CA	Tampa	FL	92	low
TRP-0004-0011	DRV-0004	DEV-0004	2025-10-26 10:34:27.261301	2025-10-26 12:00:06.666905	85.66	98.48	33.899354	-112.271786	44.458680	-117.324853	40.77	51.41	2	1	1	1	f	commute	2025-11-14 06:20:27.984465	Houston	TX	Tampa	FL	92	low
TRP-0004-0012	DRV-0004	DEV-0004	2025-11-10 19:01:27.261301	2025-11-10 19:41:32.59264	40.09	42.55	33.971322	-121.035851	32.050175	-90.588630	31.45	71.31	0	0	1	1	f	commute	2025-11-14 06:20:27.984465	Miami	NY	San Francisco	NY	74	medium
TRP-0004-0013	DRV-0004	DEV-0004	2025-10-19 22:43:27.261301	2025-10-20 00:06:58.735168	83.52	76.01	39.685695	-115.293245	37.902575	-116.252559	47.44	63.17	1	0	1	0	f	commute	2025-11-14 06:20:27.984466	Los Angeles	FL	Dallas	FL	81	low
TRP-0004-0014	DRV-0004	DEV-0004	2025-11-07 21:40:27.261301	2025-11-07 22:22:10.596095	41.72	22.00	44.595418	-93.156531	34.712417	-88.493152	28.67	65.64	1	0	1	0	f	leisure	2025-11-14 06:20:27.984466	Los Angeles	NY	San Francisco	TX	78	medium
TRP-0004-0015	DRV-0004	DEV-0004	2025-10-17 09:39:27.261301	2025-10-17 10:48:16.285578	68.82	49.16	33.473817	-102.338186	41.953163	-95.046109	48.55	55.41	0	2	1	2	f	leisure	2025-11-14 06:20:27.984466	Miami	NY	San Francisco	TX	90	low
TRP-0004-0016	DRV-0004	DEV-0004	2025-11-03 22:53:27.261301	2025-11-03 23:18:41.077271	25.23	26.87	39.714711	-117.144498	35.733500	-100.452483	27.01	48.31	0	2	1	1	f	errand	2025-11-14 06:20:27.984466	Houston	TX	Tampa	TX	76	low
TRP-0004-0017	DRV-0004	DEV-0004	2025-10-22 09:19:27.261301	2025-10-22 10:45:41.07069	86.23	75.34	33.799889	-114.062340	32.613150	-96.707815	29.06	52.25	0	1	0	0	f	errand	2025-11-14 06:20:27.984466	Miami	NY	Dallas	FL	78	medium
TRP-0004-0018	DRV-0004	DEV-0004	2025-10-31 18:28:27.261301	2025-10-31 19:46:42.964204	78.26	42.57	40.311107	-97.470738	35.429218	-80.704831	37.24	47.10	2	1	1	0	f	errand	2025-11-14 06:20:27.984467	Miami	FL	Buffalo	NY	95	medium
TRP-0004-0019	DRV-0004	DEV-0004	2025-10-19 20:40:27.261301	2025-10-19 21:29:13.289733	48.77	31.76	42.451949	-118.035612	40.312488	-106.066753	30.81	57.97	2	1	0	1	t	leisure	2025-11-14 06:20:27.984467	Houston	TX	Tampa	NY	92	low
TRP-0004-0020	DRV-0004	DEV-0004	2025-10-20 08:05:27.261301	2025-10-20 09:19:50.667479	74.39	85.31	42.104378	-120.884819	39.215151	-115.714206	28.20	47.97	0	3	1	0	f	leisure	2025-11-14 06:20:27.984467	Miami	TX	Dallas	FL	70	medium
TRP-0004-0021	DRV-0004	DEV-0004	2025-10-25 07:29:27.261301	2025-10-25 07:57:07.721965	27.67	29.64	43.371977	-109.986520	36.776508	-101.738941	36.43	59.31	0	1	0	0	f	leisure	2025-11-14 06:20:27.984467	Los Angeles	FL	Dallas	TX	95	medium
TRP-0004-0022	DRV-0004	DEV-0004	2025-10-22 18:12:27.261301	2025-10-22 19:00:47.033247	48.33	36.37	33.597658	-77.909170	36.162538	-110.314815	44.54	71.66	0	2	0	2	f	errand	2025-11-14 06:20:27.984467	Houston	CA	San Francisco	NY	80	medium
TRP-0004-0023	DRV-0004	DEV-0004	2025-11-01 08:42:27.261301	2025-11-01 09:42:46.657862	60.32	52.46	37.693001	-121.883186	32.760012	-99.471548	41.02	67.49	2	3	1	0	f	errand	2025-11-14 06:20:27.984467	Houston	NY	Buffalo	TX	70	medium
TRP-0004-0024	DRV-0004	DEV-0004	2025-10-16 07:52:27.261301	2025-10-16 09:13:23.781962	80.94	53.78	41.238005	-103.397355	41.480859	-121.947414	49.08	56.45	0	2	1	0	f	commute	2025-11-14 06:20:27.984468	Los Angeles	NY	Dallas	CA	83	low
TRP-0004-0025	DRV-0004	DEV-0004	2025-11-02 15:42:27.261301	2025-11-02 16:05:14.510794	22.79	13.84	40.864405	-106.304897	39.638383	-97.621586	52.58	45.38	2	2	1	2	f	leisure	2025-11-14 06:20:27.984468	New York	FL	Tampa	TX	74	low
TRP-0004-0026	DRV-0004	DEV-0004	2025-10-26 07:42:27.261301	2025-10-26 08:51:09.311942	68.70	69.92	39.740744	-93.167117	37.225937	-119.765615	46.34	60.57	2	1	0	0	f	leisure	2025-11-14 06:20:27.984468	Miami	TX	Buffalo	NY	95	medium
TRP-0004-0027	DRV-0004	DEV-0004	2025-10-25 16:05:27.261301	2025-10-25 17:23:18.779569	77.86	50.93	33.591912	-78.078061	36.639308	-97.171708	26.19	45.54	1	3	0	1	f	leisure	2025-11-14 06:20:27.984468	Los Angeles	CA	San Francisco	TX	85	medium
TRP-0004-0028	DRV-0004	DEV-0004	2025-11-07 14:31:27.261301	2025-11-07 16:01:26.516587	89.99	84.62	44.745750	-78.521502	36.992805	-89.611995	54.07	52.66	2	3	1	1	f	errand	2025-11-14 06:20:27.984468	Houston	FL	Tampa	TX	87	low
TRP-0004-0029	DRV-0004	DEV-0004	2025-10-14 15:49:27.261301	2025-10-14 16:23:52.518053	34.42	31.08	43.250146	-100.939886	40.589336	-108.017485	53.32	72.87	2	0	0	0	f	leisure	2025-11-14 06:20:27.984468	Houston	CA	Tampa	FL	92	medium
TRP-0004-0030	DRV-0004	DEV-0004	2025-10-28 22:32:27.261301	2025-10-28 23:35:27.192189	63.00	62.01	41.414180	-108.063732	35.772083	-74.043618	53.38	48.14	1	3	0	0	f	commute	2025-11-14 06:20:27.984469	Los Angeles	NY	San Francisco	NY	71	low
TRP-0005-0001	DRV-0005	DEV-0005	2025-10-25 21:13:27.494093	2025-10-25 21:36:43.341875	23.26	25.37	43.963219	-89.787344	35.859304	-80.806161	34.33	67.97	2	3	1	2	f	leisure	2025-11-14 06:20:27.984469	New York	NY	San Francisco	FL	89	medium
TRP-0005-0002	DRV-0005	DEV-0005	2025-10-15 22:14:27.494093	2025-10-15 22:42:38.791126	28.19	23.26	43.104648	-80.243759	35.422771	-105.112960	30.86	68.18	1	3	0	2	f	commute	2025-11-14 06:20:27.984469	New York	TX	San Francisco	TX	83	medium
TRP-0005-0003	DRV-0005	DEV-0005	2025-10-30 08:44:27.494093	2025-10-30 09:25:38.677399	41.19	38.18	36.635206	-102.434003	33.561060	-78.773728	42.81	54.67	1	0	0	1	f	commute	2025-11-14 06:20:27.984469	New York	NY	Buffalo	CA	76	medium
TRP-0005-0004	DRV-0005	DEV-0005	2025-10-31 07:58:27.494093	2025-10-31 08:19:47.749462	21.34	24.63	33.858970	-108.490177	33.827724	-119.141216	52.02	63.81	0	0	0	0	f	errand	2025-11-14 06:20:27.984469	Miami	NY	Dallas	CA	77	medium
TRP-0005-0005	DRV-0005	DEV-0005	2025-11-06 08:55:27.494093	2025-11-06 09:59:28.738453	64.02	45.60	34.891222	-90.065439	36.353689	-115.754202	26.83	48.54	1	1	1	0	f	leisure	2025-11-14 06:20:27.984469	Los Angeles	FL	Dallas	FL	80	medium
TRP-0005-0006	DRV-0005	DEV-0005	2025-11-11 21:21:27.494093	2025-11-11 21:49:53.678692	28.44	28.65	32.943665	-120.228017	41.425333	-85.112333	33.83	60.69	2	0	1	2	f	leisure	2025-11-14 06:20:27.98447	Houston	NY	Tampa	CA	90	low
TRP-0005-0007	DRV-0005	DEV-0005	2025-10-24 14:30:27.494093	2025-10-24 15:35:18.499377	64.85	64.90	32.172055	-117.248089	36.156992	-107.129609	31.88	49.34	2	3	1	1	f	leisure	2025-11-14 06:20:27.98447	New York	FL	Tampa	NY	86	low
TRP-0005-0008	DRV-0005	DEV-0005	2025-10-17 22:44:27.494093	2025-10-18 00:03:36.796142	79.16	66.80	44.828240	-92.250332	34.728507	-117.516086	54.35	64.12	2	0	1	0	t	errand	2025-11-14 06:20:27.98447	Houston	NY	Buffalo	CA	94	low
TRP-0005-0009	DRV-0005	DEV-0005	2025-11-02 16:15:27.494093	2025-11-02 16:52:03.425044	36.60	24.58	38.868496	-111.085755	44.505092	-80.085345	41.76	68.19	0	0	1	2	f	leisure	2025-11-14 06:20:27.98447	New York	TX	Dallas	TX	89	medium
TRP-0005-0010	DRV-0005	DEV-0005	2025-11-07 08:58:27.494093	2025-11-07 09:52:26.259706	53.98	61.21	43.205985	-104.685560	43.304121	-97.113820	45.69	72.47	1	1	0	2	t	errand	2025-11-14 06:20:27.98447	Houston	FL	San Francisco	CA	93	medium
TRP-0005-0011	DRV-0005	DEV-0005	2025-10-27 11:10:27.494093	2025-10-27 11:48:58.06715	38.51	25.96	39.787860	-110.397710	42.100169	-98.684233	25.20	54.87	2	0	0	2	f	leisure	2025-11-14 06:20:27.98447	Miami	TX	Tampa	TX	70	low
TRP-0005-0012	DRV-0005	DEV-0005	2025-11-03 20:07:27.494093	2025-11-03 20:54:16.902148	46.82	49.13	37.831965	-78.837815	42.138217	-74.726354	32.91	53.80	0	2	1	2	f	leisure	2025-11-14 06:20:27.984471	New York	FL	Tampa	CA	87	medium
TRP-0005-0013	DRV-0005	DEV-0005	2025-10-22 22:53:27.494093	2025-10-22 23:36:08.017017	42.68	27.55	43.441543	-96.550541	39.249172	-99.633387	25.34	45.16	1	2	1	0	f	leisure	2025-11-14 06:20:27.984471	Miami	TX	Dallas	CA	84	medium
TRP-0005-0014	DRV-0005	DEV-0005	2025-11-01 22:05:27.494093	2025-11-01 22:57:25.012751	51.96	41.20	32.352585	-112.619679	33.883116	-104.691729	39.83	47.11	1	3	0	2	f	commute	2025-11-14 06:20:27.984471	Miami	TX	Dallas	CA	72	medium
TRP-0005-0015	DRV-0005	DEV-0005	2025-10-23 19:59:27.494093	2025-10-23 21:25:16.648712	85.82	86.00	35.599974	-90.015590	40.512124	-112.934995	50.76	55.14	2	0	0	1	f	errand	2025-11-14 06:20:27.984471	Los Angeles	TX	San Francisco	TX	73	low
TRP-0005-0016	DRV-0005	DEV-0005	2025-11-04 13:27:27.494093	2025-11-04 14:05:11.527425	37.73	38.43	33.463707	-116.888654	33.710464	-96.478901	42.04	45.11	0	0	0	0	f	errand	2025-11-14 06:20:27.984471	Miami	NY	San Francisco	NY	79	medium
TRP-0005-0017	DRV-0005	DEV-0005	2025-10-22 21:05:27.494093	2025-10-22 21:32:12.596306	26.75	28.78	34.847408	-121.324594	43.420151	-93.427032	48.60	71.89	0	3	1	2	f	leisure	2025-11-14 06:20:27.984472	New York	NY	Dallas	NY	86	medium
TRP-0005-0018	DRV-0005	DEV-0005	2025-10-23 11:20:27.494093	2025-10-23 12:10:54.109361	50.44	48.03	35.109579	-106.879315	32.224872	-104.355475	28.84	64.33	0	1	1	1	f	commute	2025-11-14 06:20:27.984472	New York	CA	Buffalo	TX	71	low
TRP-0005-0019	DRV-0005	DEV-0005	2025-11-10 17:25:27.494093	2025-11-10 17:40:54.468611	15.45	13.64	35.384323	-99.668278	35.711318	-95.786377	41.46	68.24	2	2	0	0	f	leisure	2025-11-14 06:20:27.984472	New York	TX	San Francisco	FL	79	medium
TRP-0005-0020	DRV-0005	DEV-0005	2025-10-22 11:32:27.494093	2025-10-22 12:22:05.255572	49.63	30.54	41.103551	-85.390946	41.596501	-85.426491	29.62	66.67	0	1	1	1	f	commute	2025-11-14 06:20:27.984472	Miami	NY	Dallas	NY	74	low
TRP-0005-0021	DRV-0005	DEV-0005	2025-10-21 09:46:27.494093	2025-10-21 10:59:56.766098	73.49	67.04	42.853295	-102.650962	35.284114	-78.432010	45.95	49.22	2	2	0	2	f	leisure	2025-11-14 06:20:27.984472	New York	TX	San Francisco	FL	84	medium
TRP-0005-0022	DRV-0005	DEV-0005	2025-11-12 20:23:27.494093	2025-11-12 21:12:08.183389	48.68	42.42	40.137203	-82.188694	33.267927	-74.377583	42.78	67.35	0	3	1	1	f	leisure	2025-11-14 06:20:27.984472	Los Angeles	FL	Dallas	CA	76	medium
TRP-0005-0023	DRV-0005	DEV-0005	2025-10-24 15:46:27.494093	2025-10-24 16:05:51.073645	19.39	13.05	41.262465	-114.158296	33.213550	-86.700325	41.44	61.24	1	0	0	1	f	leisure	2025-11-14 06:20:27.984473	Houston	CA	Buffalo	TX	93	low
TRP-0005-0024	DRV-0005	DEV-0005	2025-10-19 14:28:27.494093	2025-10-19 15:27:55.535814	59.47	60.33	41.204161	-106.639747	38.235377	-89.481427	47.65	72.53	1	2	0	0	t	errand	2025-11-14 06:20:27.984473	Miami	TX	Dallas	CA	85	low
TRP-0005-0025	DRV-0005	DEV-0005	2025-10-19 20:26:27.494093	2025-10-19 21:44:25.234887	77.96	49.62	38.736989	-80.774256	44.133341	-78.852936	45.60	71.83	1	0	1	1	f	leisure	2025-11-14 06:20:27.984473	New York	TX	San Francisco	CA	92	low
TRP-0005-0026	DRV-0005	DEV-0005	2025-11-10 20:10:27.494093	2025-11-10 20:36:26.339491	25.98	22.96	36.315608	-74.104460	40.499401	-100.469617	42.05	68.52	1	0	0	2	f	errand	2025-11-14 06:20:27.984473	Houston	FL	Tampa	CA	91	low
TRP-0005-0027	DRV-0005	DEV-0005	2025-10-15 22:48:27.494093	2025-10-15 23:08:25.107142	19.96	14.91	32.788763	-118.943181	39.686111	-82.092467	35.61	71.76	2	0	0	1	f	commute	2025-11-14 06:20:27.984473	Houston	FL	Buffalo	CA	81	low
TRP-0005-0028	DRV-0005	DEV-0005	2025-11-05 10:42:27.494093	2025-11-05 10:57:53.308005	15.43	7.97	44.281802	-107.117475	37.127370	-101.693473	50.77	50.77	2	2	1	1	t	errand	2025-11-14 06:20:27.984473	Miami	TX	Buffalo	NY	82	low
TRP-0005-0029	DRV-0005	DEV-0005	2025-10-23 19:08:27.494093	2025-10-23 20:23:54.954967	75.46	90.44	42.864853	-110.341942	38.061940	-95.205928	46.51	60.43	0	1	0	1	f	leisure	2025-11-14 06:20:27.984474	Los Angeles	FL	Tampa	TX	84	low
TRP-0005-0030	DRV-0005	DEV-0005	2025-10-30 13:00:27.494093	2025-10-30 13:46:16.019277	45.81	25.78	37.951375	-100.710217	41.043215	-83.743718	54.64	51.35	2	2	0	2	f	leisure	2025-11-14 06:20:27.984474	Houston	CA	San Francisco	TX	87	medium
TRP-0006-0001	DRV-0006	DEV-0006	2025-11-12 21:58:27.730179	2025-11-12 22:22:39.766472	24.20	25.81	42.367432	-112.011029	39.101238	-76.707155	31.32	56.77	1	3	0	0	f	commute	2025-11-14 06:20:27.984474	New York	TX	San Francisco	CA	75	low
TRP-0006-0002	DRV-0006	DEV-0006	2025-10-31 12:56:27.730179	2025-10-31 14:20:11.411316	83.73	63.79	34.751677	-118.492959	44.225035	-82.693419	26.85	65.19	1	0	1	2	f	errand	2025-11-14 06:20:27.984474	New York	TX	Dallas	NY	86	low
TRP-0006-0003	DRV-0006	DEV-0006	2025-11-07 20:43:27.730179	2025-11-07 21:09:59.706997	26.53	31.19	33.855508	-74.202922	44.662789	-76.907874	39.79	68.71	2	0	0	2	f	leisure	2025-11-14 06:20:27.984474	New York	TX	Dallas	FL	94	low
TRP-0006-0004	DRV-0006	DEV-0006	2025-10-27 19:29:27.730179	2025-10-27 19:57:19.39833	27.86	31.32	32.478466	-84.746783	40.135041	-101.063164	26.39	45.76	2	0	1	2	f	commute	2025-11-14 06:20:27.984475	New York	TX	San Francisco	TX	85	medium
TRP-0006-0005	DRV-0006	DEV-0006	2025-10-29 18:22:27.730179	2025-10-29 19:19:49.052478	57.36	67.62	44.986694	-103.708532	42.705701	-97.239048	52.36	57.56	1	1	0	1	f	leisure	2025-11-14 06:20:27.984475	New York	NY	Buffalo	TX	88	medium
TRP-0006-0006	DRV-0006	DEV-0006	2025-11-02 14:01:27.730179	2025-11-02 14:31:18.405597	29.84	23.53	36.256691	-78.479219	40.434109	-116.126766	47.36	65.00	0	2	0	0	f	commute	2025-11-14 06:20:27.984475	Houston	CA	Tampa	NY	85	medium
TRP-0006-0007	DRV-0006	DEV-0006	2025-10-25 18:19:27.730179	2025-10-25 19:18:50.815209	59.38	47.22	35.243614	-88.452461	42.488335	-95.103549	54.15	60.55	1	2	1	1	f	commute	2025-11-14 06:20:27.984475	Miami	CA	San Francisco	CA	81	low
TRP-0006-0008	DRV-0006	DEV-0006	2025-10-31 00:13:27.730179	2025-10-31 01:01:29.738958	48.03	52.58	44.168930	-112.145837	43.923668	-79.792513	40.88	52.84	2	1	1	1	f	leisure	2025-11-14 06:20:27.984475	Miami	TX	San Francisco	NY	90	medium
TRP-0006-0009	DRV-0006	DEV-0006	2025-10-16 08:14:27.730179	2025-10-16 08:34:31.918318	20.07	16.08	34.408089	-95.121184	33.183968	-102.280335	43.39	71.04	2	2	0	1	f	errand	2025-11-14 06:20:27.984475	Los Angeles	CA	Dallas	NY	75	medium
TRP-0006-0010	DRV-0006	DEV-0006	2025-10-22 16:33:27.730179	2025-10-22 18:01:03.064306	87.59	54.47	32.407697	-105.328399	40.734268	-113.498095	34.37	64.31	0	1	0	1	f	commute	2025-11-14 06:20:27.984476	Los Angeles	CA	Dallas	NY	93	low
TRP-0006-0011	DRV-0006	DEV-0006	2025-10-15 20:16:27.730179	2025-10-15 21:15:19.634919	58.87	50.90	38.870545	-120.766978	44.977128	-94.361332	49.49	53.76	2	1	0	2	f	commute	2025-11-14 06:20:27.984476	Miami	FL	Buffalo	NY	78	low
TRP-0006-0012	DRV-0006	DEV-0006	2025-10-17 11:08:27.730179	2025-10-17 12:11:21.740722	62.90	35.50	32.514599	-117.457180	32.563286	-103.523322	43.66	47.77	0	1	1	0	f	leisure	2025-11-14 06:20:27.984476	New York	FL	San Francisco	TX	77	medium
TRP-0006-0013	DRV-0006	DEV-0006	2025-11-05 20:14:27.730179	2025-11-05 20:35:37.515847	21.16	22.29	33.424471	-77.711922	33.476090	-119.363978	48.60	63.39	0	1	0	2	f	leisure	2025-11-14 06:20:27.984476	Los Angeles	CA	Tampa	TX	70	low
TRP-0006-0014	DRV-0006	DEV-0006	2025-10-21 10:49:27.730179	2025-10-21 11:42:13.543963	52.76	53.74	37.172503	-90.406018	33.364067	-83.276310	47.21	50.48	2	2	1	1	f	leisure	2025-11-14 06:20:27.984476	Houston	TX	San Francisco	CA	80	medium
TRP-0006-0015	DRV-0006	DEV-0006	2025-10-30 10:07:27.730179	2025-10-30 11:10:24.589445	62.95	63.71	42.692539	-117.216685	37.700082	-75.974344	47.23	60.48	2	1	0	1	f	errand	2025-11-14 06:20:27.984476	Houston	TX	San Francisco	NY	78	low
TRP-0006-0016	DRV-0006	DEV-0006	2025-10-19 19:13:27.730179	2025-10-19 20:03:58.75926	50.52	57.44	36.769146	-114.622426	37.416045	-110.964486	29.15	51.98	0	1	0	2	f	errand	2025-11-14 06:20:27.984477	New York	CA	Buffalo	CA	89	medium
TRP-0006-0017	DRV-0006	DEV-0006	2025-11-03 14:48:27.730179	2025-11-03 15:32:43.57448	44.26	42.26	37.524304	-114.318979	42.171837	-102.144748	44.89	52.09	0	1	1	2	f	leisure	2025-11-14 06:20:27.98448	New York	NY	Buffalo	FL	80	low
TRP-0006-0018	DRV-0006	DEV-0006	2025-10-16 21:17:27.730179	2025-10-16 21:59:23.316617	41.93	25.20	37.403273	-119.275294	38.099237	-92.335606	27.05	47.93	1	2	1	0	f	commute	2025-11-14 06:20:27.98448	Los Angeles	TX	San Francisco	CA	94	medium
TRP-0006-0019	DRV-0006	DEV-0006	2025-11-05 15:29:27.730179	2025-11-05 16:13:09.73986	43.70	46.68	39.161537	-92.567983	32.532435	-74.394263	51.57	48.13	0	0	1	0	f	commute	2025-11-14 06:20:27.984481	Los Angeles	NY	Tampa	NY	93	medium
TRP-0006-0020	DRV-0006	DEV-0006	2025-11-03 17:11:27.730179	2025-11-03 17:31:18.181872	19.84	10.87	33.711585	-109.413755	44.616026	-118.195242	45.07	48.35	2	2	0	1	f	leisure	2025-11-14 06:20:27.984481	Miami	NY	Dallas	TX	89	medium
TRP-0006-0021	DRV-0006	DEV-0006	2025-11-04 18:03:27.730179	2025-11-04 18:30:40.853395	27.22	25.19	35.349815	-120.615331	33.668933	-95.249552	31.09	45.29	1	1	1	2	f	commute	2025-11-14 06:20:27.984481	Houston	TX	Tampa	NY	76	medium
TRP-0006-0022	DRV-0006	DEV-0006	2025-10-27 18:35:27.730179	2025-10-27 19:29:24.435932	53.95	39.46	38.175707	-102.431757	42.430440	-82.802120	41.28	74.11	2	0	0	1	f	leisure	2025-11-14 06:20:27.984481	Miami	CA	Dallas	FL	94	low
TRP-0006-0023	DRV-0006	DEV-0006	2025-10-25 07:39:27.730179	2025-10-25 08:39:43.967061	60.27	38.67	40.800086	-93.039294	39.338545	-80.733755	42.66	48.81	0	3	1	1	t	errand	2025-11-14 06:20:27.984481	Miami	FL	Buffalo	CA	92	low
TRP-0006-0024	DRV-0006	DEV-0006	2025-10-21 12:28:27.730179	2025-10-21 12:51:43.709306	23.27	15.50	34.503122	-99.547055	36.940113	-98.267746	53.77	61.84	1	2	0	1	f	commute	2025-11-14 06:20:27.984481	Los Angeles	TX	Buffalo	TX	70	low
TRP-0006-0025	DRV-0006	DEV-0006	2025-11-03 19:51:27.730179	2025-11-03 20:44:41.680249	53.23	34.81	32.285462	-89.540781	43.650315	-114.343206	47.66	72.57	0	0	0	1	f	leisure	2025-11-14 06:20:27.984482	Los Angeles	FL	Dallas	TX	86	low
TRP-0006-0026	DRV-0006	DEV-0006	2025-10-19 19:39:27.730179	2025-10-19 20:05:28.783631	26.02	23.04	43.591638	-76.634520	44.941884	-83.350881	34.14	56.02	2	2	0	0	f	commute	2025-11-14 06:20:27.984482	Houston	TX	Tampa	FL	93	low
TRP-0006-0027	DRV-0006	DEV-0006	2025-10-31 09:18:27.730179	2025-10-31 10:40:00.499861	81.55	54.34	32.626427	-78.225233	32.920904	-100.882042	54.68	50.57	2	0	1	1	t	leisure	2025-11-14 06:20:27.984482	Los Angeles	TX	Tampa	TX	82	medium
TRP-0006-0028	DRV-0006	DEV-0006	2025-11-03 07:43:27.730179	2025-11-03 09:07:38.606988	84.18	61.12	43.725745	-91.409455	38.094795	-78.785931	29.19	54.36	1	2	0	1	f	errand	2025-11-14 06:20:27.984482	Los Angeles	CA	Tampa	CA	91	medium
TRP-0006-0029	DRV-0006	DEV-0006	2025-10-30 07:50:27.730179	2025-10-30 09:19:26.97981	88.99	104.43	42.647151	-82.540253	42.169224	-102.132787	36.94	71.37	0	1	1	2	f	commute	2025-11-14 06:20:27.984482	Miami	CA	Buffalo	FL	86	low
TRP-0006-0030	DRV-0006	DEV-0006	2025-10-19 18:34:27.730179	2025-10-19 19:09:29.459099	35.03	41.69	43.499222	-105.840030	42.733504	-118.854774	37.03	64.46	0	3	1	0	f	leisure	2025-11-14 06:20:27.984482	Houston	NY	San Francisco	CA	81	medium
TRP-0007-0001	DRV-0007	DEV-0007	2025-10-16 19:25:27.968752	2025-10-16 19:55:26.686318	29.98	26.51	39.001417	-107.413291	41.663459	-77.739475	44.96	73.56	1	3	1	2	f	errand	2025-11-14 06:20:27.984483	New York	CA	Dallas	CA	85	low
TRP-0007-0002	DRV-0007	DEV-0007	2025-11-05 10:13:27.968752	2025-11-05 10:34:38.403481	21.17	18.38	36.433464	-85.251038	43.335993	-85.694043	27.05	69.01	0	3	1	0	f	errand	2025-11-14 06:20:27.984483	Los Angeles	CA	Tampa	NY	86	low
TRP-0007-0003	DRV-0007	DEV-0007	2025-10-29 17:48:27.968752	2025-10-29 18:12:14.929391	23.78	15.50	36.521051	-74.793396	41.988102	-102.824168	35.71	68.39	1	2	1	2	f	leisure	2025-11-14 06:20:27.984483	Los Angeles	CA	Dallas	CA	76	low
TRP-0007-0004	DRV-0007	DEV-0007	2025-11-11 10:39:27.968752	2025-11-11 11:06:56.812957	27.48	15.52	35.076580	-106.158508	36.634039	-88.033987	30.21	56.96	0	3	1	1	f	commute	2025-11-14 06:20:27.984483	Houston	TX	Tampa	FL	89	low
TRP-0007-0005	DRV-0007	DEV-0007	2025-11-08 16:34:27.968752	2025-11-08 17:26:01.878109	51.57	44.21	38.356950	-106.116285	35.480073	-96.438055	42.53	46.97	0	2	0	1	f	errand	2025-11-14 06:20:27.984483	New York	TX	Tampa	NY	87	medium
TRP-0007-0006	DRV-0007	DEV-0007	2025-11-12 19:17:27.968752	2025-11-12 20:12:38.831656	55.18	48.99	32.244612	-118.097703	36.350361	-92.691159	47.88	67.95	1	0	0	1	f	leisure	2025-11-14 06:20:27.984483	New York	NY	Dallas	TX	89	low
TRP-0007-0007	DRV-0007	DEV-0007	2025-10-25 16:42:27.968752	2025-10-25 17:52:27.356601	69.99	56.77	41.175333	-90.765925	44.886477	-85.328917	41.25	54.31	2	3	1	1	f	commute	2025-11-14 06:20:27.984484	New York	TX	Buffalo	TX	95	medium
TRP-0007-0008	DRV-0007	DEV-0007	2025-10-19 21:26:27.968752	2025-10-19 22:52:18.31964	85.84	92.58	36.529533	-96.323495	37.610879	-87.881571	50.09	61.91	0	2	0	1	f	leisure	2025-11-14 06:20:27.984484	Houston	CA	Dallas	FL	79	medium
TRP-0007-0009	DRV-0007	DEV-0007	2025-11-02 21:16:27.968752	2025-11-02 22:00:31.827461	44.06	42.74	42.676453	-97.012089	37.717580	-83.407538	34.26	54.90	2	3	1	1	f	leisure	2025-11-14 06:20:27.984484	Los Angeles	TX	San Francisco	TX	83	medium
TRP-0007-0010	DRV-0007	DEV-0007	2025-10-24 17:13:27.968752	2025-10-24 18:35:09.066705	81.68	44.30	39.240787	-76.359512	36.717463	-75.782754	46.50	53.11	2	3	1	1	f	errand	2025-11-14 06:20:27.984484	New York	NY	Tampa	TX	78	medium
TRP-0007-0011	DRV-0007	DEV-0007	2025-10-29 11:48:27.968752	2025-10-29 13:02:13.899625	73.77	51.30	38.866653	-107.902279	38.660449	-109.624122	37.22	49.18	1	0	0	2	f	errand	2025-11-14 06:20:27.984484	Los Angeles	TX	San Francisco	NY	77	medium
TRP-0007-0012	DRV-0007	DEV-0007	2025-10-16 18:04:27.968752	2025-10-16 18:38:24.075455	33.94	39.68	42.861618	-77.294497	33.050874	-102.650950	28.80	47.61	2	2	0	0	f	leisure	2025-11-14 06:20:27.984484	Los Angeles	CA	Tampa	TX	92	low
TRP-0007-0013	DRV-0007	DEV-0007	2025-10-29 16:51:27.968752	2025-10-29 17:10:40.782526	19.21	13.28	40.649711	-107.819534	40.096824	-74.372881	36.20	52.97	0	0	0	2	f	errand	2025-11-14 06:20:27.984485	New York	FL	Buffalo	TX	94	medium
TRP-0007-0014	DRV-0007	DEV-0007	2025-11-09 17:27:27.968752	2025-11-09 17:54:39.898209	27.20	19.23	36.263908	-98.278122	35.842053	-105.621124	35.25	54.12	2	1	1	2	f	errand	2025-11-14 06:20:27.984485	Los Angeles	CA	Tampa	NY	72	medium
TRP-0007-0015	DRV-0007	DEV-0007	2025-11-07 19:42:27.968752	2025-11-07 20:22:38.549412	40.18	39.97	42.851097	-80.670869	36.217889	-93.801847	53.32	67.88	0	0	0	1	f	errand	2025-11-14 06:20:27.984485	Los Angeles	NY	Buffalo	NY	72	medium
TRP-0007-0016	DRV-0007	DEV-0007	2025-11-11 20:35:27.968752	2025-11-11 21:51:48.042189	76.33	73.08	39.555431	-119.336166	41.567548	-87.415770	43.80	69.64	1	3	0	1	f	errand	2025-11-14 06:20:27.984485	Miami	CA	Tampa	CA	83	low
TRP-0007-0017	DRV-0007	DEV-0007	2025-10-20 20:17:27.968752	2025-10-20 20:53:37.991252	36.17	38.79	33.383043	-117.981294	36.117621	-113.117127	50.34	69.90	0	1	1	2	f	commute	2025-11-14 06:20:27.984485	Houston	CA	Buffalo	CA	78	low
TRP-0007-0018	DRV-0007	DEV-0007	2025-10-30 21:27:27.968752	2025-10-30 22:13:35.604292	46.13	35.87	40.242739	-76.865714	33.420342	-97.825629	34.37	46.29	2	1	0	1	f	commute	2025-11-14 06:20:27.984485	Miami	TX	San Francisco	FL	95	medium
TRP-0007-0019	DRV-0007	DEV-0007	2025-11-03 13:11:27.968752	2025-11-03 14:36:27.310218	84.99	49.93	44.003463	-83.922601	39.063862	-102.508931	34.08	69.55	2	2	0	0	t	leisure	2025-11-14 06:20:27.984486	Miami	FL	San Francisco	NY	74	medium
TRP-0007-0020	DRV-0007	DEV-0007	2025-10-14 16:04:27.968752	2025-10-14 16:25:09.653554	20.69	18.97	41.936126	-98.462185	40.445427	-91.710173	46.68	65.66	1	2	1	1	f	leisure	2025-11-14 06:20:27.984486	Los Angeles	FL	Tampa	TX	91	low
TRP-0007-0021	DRV-0007	DEV-0007	2025-11-01 10:25:27.968752	2025-11-01 10:58:19.269803	32.86	31.86	32.966605	-107.333296	40.958350	-108.698144	27.60	59.01	1	1	1	0	f	leisure	2025-11-14 06:20:27.984486	Los Angeles	FL	San Francisco	FL	80	medium
TRP-0007-0022	DRV-0007	DEV-0007	2025-10-27 09:48:27.968752	2025-10-27 10:04:12.316272	15.74	11.77	36.555893	-91.587185	33.955408	-118.558309	27.14	46.07	2	1	1	1	f	errand	2025-11-14 06:20:27.984486	Los Angeles	NY	Dallas	TX	90	medium
TRP-0007-0023	DRV-0007	DEV-0007	2025-10-24 23:08:27.968752	2025-10-25 00:07:24.122168	58.94	46.22	35.835487	-98.213468	42.033218	-99.693852	37.17	73.11	0	2	1	2	f	errand	2025-11-14 06:20:27.984486	Los Angeles	TX	Buffalo	TX	76	low
TRP-0007-0024	DRV-0007	DEV-0007	2025-11-12 16:11:27.968752	2025-11-12 16:39:15.003261	27.78	29.80	43.341076	-120.295058	41.079367	-114.412310	44.42	66.76	0	2	0	0	f	commute	2025-11-14 06:20:27.984486	New York	CA	Buffalo	NY	76	low
TRP-0007-0025	DRV-0007	DEV-0007	2025-10-23 12:56:27.968752	2025-10-23 14:14:14.853474	77.78	69.41	40.175000	-108.993323	44.596056	-91.697353	30.67	62.44	0	1	1	0	f	leisure	2025-11-14 06:20:27.984487	Houston	TX	Buffalo	FL	80	medium
TRP-0007-0026	DRV-0007	DEV-0007	2025-11-03 16:38:27.968752	2025-11-03 17:31:04.544849	52.61	42.15	41.080651	-117.930325	44.765206	-108.755388	27.62	64.20	0	3	1	1	t	leisure	2025-11-14 06:20:27.984487	Houston	FL	Tampa	CA	94	low
TRP-0007-0027	DRV-0007	DEV-0007	2025-10-17 09:02:27.968752	2025-10-17 10:07:45.309581	65.29	34.18	37.348530	-99.386397	43.721715	-80.294611	42.25	45.67	1	1	0	2	f	leisure	2025-11-14 06:20:27.984487	Miami	TX	Tampa	NY	75	low
TRP-0007-0028	DRV-0007	DEV-0007	2025-11-11 22:00:27.968752	2025-11-11 22:29:06.990841	28.65	28.08	38.859374	-81.508556	36.061821	-93.809765	54.43	45.83	0	2	1	0	f	errand	2025-11-14 06:20:27.984487	Los Angeles	TX	Tampa	TX	92	medium
TRP-0007-0029	DRV-0007	DEV-0007	2025-11-07 13:23:27.968752	2025-11-07 14:29:58.961013	66.52	39.89	35.478965	-97.746433	43.344761	-89.633437	53.99	59.89	2	3	0	1	f	leisure	2025-11-14 06:20:27.984487	Houston	FL	Tampa	FL	70	low
TRP-0007-0030	DRV-0007	DEV-0007	2025-10-22 15:12:27.968752	2025-10-22 16:15:26.29828	62.97	55.21	35.777836	-91.575635	33.640541	-119.928549	37.67	63.09	0	0	1	0	f	leisure	2025-11-14 06:20:27.984487	New York	CA	Buffalo	FL	79	low
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.users (user_id, driver_id, username, email, hashed_password, is_active, is_admin, last_login, created_at, updated_at) FROM stdin;
3	DRV-0002	driver0002	mary.johnson@example.com	$2b$12$mGZLo5E7soQofi6YoAdIQe8KwdEZqTD4ZOv1KFtWIJoFfIucncnpa	t	f	\N	2025-11-14 06:20:27.979418	2025-11-14 06:20:27.979419
4	DRV-0003	driver0003	john.williams@example.com	$2b$12$OeNrnFI8BBcDA/K8N9EphuC.V3NifN76NZMA56Bdxklm5UtL0zCEa	t	f	\N	2025-11-14 06:20:27.979419	2025-11-14 06:20:27.979419
5	DRV-0004	driver0004	patricia.brown@example.com	$2b$12$7uSHHGl1ZPecRspvW5GZQu8NoREPgMC3yM5T9tnlE/qq.R1ifkZcC	t	f	\N	2025-11-14 06:20:27.979419	2025-11-14 06:20:27.97942
6	DRV-0005	driver0005	robert.jones@example.com	$2b$12$MbrKWCdJxs1Fsu7M4mBwPe5tjs1N2sa3x0kjqo6yoHL0DWchLXiTK	t	f	\N	2025-11-14 06:20:27.97942	2025-11-14 06:20:27.97942
7	DRV-0006	driver0006	jennifer.garcia@example.com	$2b$12$4BlP/EQ4FxhCpSyI/Zhf2.E7DQe58Pu0.lFgR2oVVp0t5MMuubcBK	t	f	\N	2025-11-14 06:20:27.97942	2025-11-14 06:20:27.97942
8	DRV-0007	driver0007	michael.miller@example.com	$2b$12$qoGOizm1i2rxAr2r7CFjnutU8jqATOahhizMK2X3/ru40rz2kRWvO	t	f	\N	2025-11-14 06:20:27.97942	2025-11-14 06:20:27.979421
1	\N	admin	admin@example.com	$2b$12$ySJQ5jirU09/VdE3JjdJSetYxPU1ziyzDvJ9LFoRMPD2uZMHBrs/i	t	t	2025-11-14 06:44:36.836762	2025-11-14 06:10:14.801158	2025-11-14 06:44:36.535777
2	DRV-0001	driver0001	james.smith@example.com	$2b$12$pTdP75ANbKqr0TSxiNkX1eDNP9pOMan4arxABMWdTB/XY/Fr7a//q	t	f	2025-11-14 06:46:02.241841	2025-11-14 06:19:09.840985	2025-11-14 06:46:01.992162
\.


--
-- Data for Name: vehicles; Type: TABLE DATA; Schema: public; Owner: insurance_user
--

COPY public.vehicles (vehicle_id, driver_id, make, model, year, vin, vehicle_type, safety_rating, created_at, updated_at) FROM stdin;
VEH-0001	DRV-0001	Ford	Edge	2022	20998177220631492	truck	5	2025-11-14 06:19:09.848471	2025-11-14 06:19:09.848473
VEH-0002	DRV-0002	Tesla	Model 3	2020	83162123275826273	suv	4	2025-11-14 06:20:27.980283	2025-11-14 06:20:27.980284
VEH-0003	DRV-0003	Toyota	Corolla	2018	46550856363605836	truck	5	2025-11-14 06:20:27.980284	2025-11-14 06:20:27.980284
VEH-0004	DRV-0004	Honda	Accord	2020	24446171571389423	truck	3	2025-11-14 06:20:27.980285	2025-11-14 06:20:27.980285
VEH-0005	DRV-0005	Ford	Escape	2023	50052429322142234	truck	3	2025-11-14 06:20:27.980285	2025-11-14 06:20:27.980285
VEH-0006	DRV-0006	Honda	Civic	2018	15418354951689242	suv	4	2025-11-14 06:20:27.980286	2025-11-14 06:20:27.980287
VEH-0007	DRV-0007	Honda	Accord	2018	19660929947976409	sedan	5	2025-11-14 06:20:27.980287	2025-11-14 06:20:27.980287
\.


--
-- Name: driver_statistics_stat_id_seq; Type: SEQUENCE SET; Schema: public; Owner: insurance_user
--

SELECT pg_catalog.setval('public.driver_statistics_stat_id_seq', 1, false);


--
-- Name: premiums_premium_id_seq; Type: SEQUENCE SET; Schema: public; Owner: insurance_user
--

SELECT pg_catalog.setval('public.premiums_premium_id_seq', 7, true);


--
-- Name: risk_scores_score_id_seq; Type: SEQUENCE SET; Schema: public; Owner: insurance_user
--

SELECT pg_catalog.setval('public.risk_scores_score_id_seq', 8, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: insurance_user
--

SELECT pg_catalog.setval('public.users_user_id_seq', 8, true);


--
-- Name: claims claims_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.claims
    ADD CONSTRAINT claims_pkey PRIMARY KEY (claim_id);


--
-- Name: devices devices_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (device_id);


--
-- Name: driver_statistics driver_statistics_driver_id_period_start_period_end_key; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.driver_statistics
    ADD CONSTRAINT driver_statistics_driver_id_period_start_period_end_key UNIQUE (driver_id, period_start, period_end);


--
-- Name: driver_statistics driver_statistics_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.driver_statistics
    ADD CONSTRAINT driver_statistics_pkey PRIMARY KEY (stat_id);


--
-- Name: drivers drivers_email_key; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_email_key UNIQUE (email);


--
-- Name: drivers drivers_license_number_key; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_license_number_key UNIQUE (license_number);


--
-- Name: drivers drivers_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.drivers
    ADD CONSTRAINT drivers_pkey PRIMARY KEY (driver_id);


--
-- Name: premiums premiums_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.premiums
    ADD CONSTRAINT premiums_pkey PRIMARY KEY (premium_id);


--
-- Name: risk_scores risk_scores_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.risk_scores
    ADD CONSTRAINT risk_scores_pkey PRIMARY KEY (score_id);


--
-- Name: telematics_events telematics_events_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events
    ADD CONSTRAINT telematics_events_pkey PRIMARY KEY (event_id, "timestamp");


--
-- Name: telematics_events_2024_11 telematics_events_2024_11_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events_2024_11
    ADD CONSTRAINT telematics_events_2024_11_pkey PRIMARY KEY (event_id, "timestamp");


--
-- Name: telematics_events_2024_12 telematics_events_2024_12_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events_2024_12
    ADD CONSTRAINT telematics_events_2024_12_pkey PRIMARY KEY (event_id, "timestamp");


--
-- Name: telematics_events_2025_01 telematics_events_2025_01_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events_2025_01
    ADD CONSTRAINT telematics_events_2025_01_pkey PRIMARY KEY (event_id, "timestamp");


--
-- Name: telematics_events_2025_09 telematics_events_2025_09_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events_2025_09
    ADD CONSTRAINT telematics_events_2025_09_pkey PRIMARY KEY (event_id, "timestamp");


--
-- Name: telematics_events_2025_10 telematics_events_2025_10_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.telematics_events_2025_10
    ADD CONSTRAINT telematics_events_2025_10_pkey PRIMARY KEY (event_id, "timestamp");


--
-- Name: trips trips_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_pkey PRIMARY KEY (trip_id);


--
-- Name: users users_driver_id_key; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_driver_id_key UNIQUE (driver_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: vehicles vehicles_pkey; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_pkey PRIMARY KEY (vehicle_id);


--
-- Name: vehicles vehicles_vin_key; Type: CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_vin_key UNIQUE (vin);


--
-- Name: idx_driver_stats_driver_id; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_driver_stats_driver_id ON public.driver_statistics USING btree (driver_id);


--
-- Name: idx_events_driver_id; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_events_driver_id ON ONLY public.telematics_events USING btree (driver_id);


--
-- Name: idx_events_timestamp; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_events_timestamp ON ONLY public.telematics_events USING btree ("timestamp");


--
-- Name: idx_events_trip_id; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_events_trip_id ON ONLY public.telematics_events USING btree (trip_id);


--
-- Name: idx_premiums_driver_id; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_premiums_driver_id ON public.premiums USING btree (driver_id);


--
-- Name: idx_premiums_driver_status; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_premiums_driver_status ON public.premiums USING btree (driver_id, status);


--
-- Name: idx_premiums_policy_type; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_premiums_policy_type ON public.premiums USING btree (policy_type);


--
-- Name: idx_premiums_status; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_premiums_status ON public.premiums USING btree (status);


--
-- Name: idx_risk_scores_calculation_date; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_risk_scores_calculation_date ON public.risk_scores USING btree (calculation_date DESC);


--
-- Name: idx_risk_scores_date; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_risk_scores_date ON public.risk_scores USING btree (calculation_date);


--
-- Name: idx_risk_scores_driver_date; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_risk_scores_driver_date ON public.risk_scores USING btree (driver_id, calculation_date DESC);


--
-- Name: idx_risk_scores_driver_id; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_risk_scores_driver_id ON public.risk_scores USING btree (driver_id);


--
-- Name: idx_trips_destination_city; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_trips_destination_city ON public.trips USING btree (destination_city);


--
-- Name: idx_trips_driver_id; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_trips_driver_id ON public.trips USING btree (driver_id);


--
-- Name: idx_trips_driver_risk_level; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_trips_driver_risk_level ON public.trips USING btree (driver_id, risk_level) WHERE (risk_level IS NOT NULL);


--
-- Name: idx_trips_driver_start_time; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_trips_driver_start_time ON public.trips USING btree (driver_id, start_time DESC);


--
-- Name: idx_trips_origin_city; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_trips_origin_city ON public.trips USING btree (origin_city);


--
-- Name: idx_trips_risk_level; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_trips_risk_level ON public.trips USING btree (risk_level);


--
-- Name: idx_trips_start_time; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_trips_start_time ON public.trips USING btree (start_time);


--
-- Name: idx_trips_trip_score; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX idx_trips_trip_score ON public.trips USING btree (trip_score);


--
-- Name: telematics_events_2024_11_driver_id_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2024_11_driver_id_idx ON public.telematics_events_2024_11 USING btree (driver_id);


--
-- Name: telematics_events_2024_11_timestamp_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2024_11_timestamp_idx ON public.telematics_events_2024_11 USING btree ("timestamp");


--
-- Name: telematics_events_2024_11_trip_id_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2024_11_trip_id_idx ON public.telematics_events_2024_11 USING btree (trip_id);


--
-- Name: telematics_events_2024_12_driver_id_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2024_12_driver_id_idx ON public.telematics_events_2024_12 USING btree (driver_id);


--
-- Name: telematics_events_2024_12_timestamp_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2024_12_timestamp_idx ON public.telematics_events_2024_12 USING btree ("timestamp");


--
-- Name: telematics_events_2024_12_trip_id_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2024_12_trip_id_idx ON public.telematics_events_2024_12 USING btree (trip_id);


--
-- Name: telematics_events_2025_01_driver_id_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2025_01_driver_id_idx ON public.telematics_events_2025_01 USING btree (driver_id);


--
-- Name: telematics_events_2025_01_timestamp_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2025_01_timestamp_idx ON public.telematics_events_2025_01 USING btree ("timestamp");


--
-- Name: telematics_events_2025_01_trip_id_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2025_01_trip_id_idx ON public.telematics_events_2025_01 USING btree (trip_id);


--
-- Name: telematics_events_2025_09_driver_id_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2025_09_driver_id_idx ON public.telematics_events_2025_09 USING btree (driver_id);


--
-- Name: telematics_events_2025_09_timestamp_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2025_09_timestamp_idx ON public.telematics_events_2025_09 USING btree ("timestamp");


--
-- Name: telematics_events_2025_09_trip_id_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2025_09_trip_id_idx ON public.telematics_events_2025_09 USING btree (trip_id);


--
-- Name: telematics_events_2025_10_driver_id_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2025_10_driver_id_idx ON public.telematics_events_2025_10 USING btree (driver_id);


--
-- Name: telematics_events_2025_10_timestamp_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2025_10_timestamp_idx ON public.telematics_events_2025_10 USING btree ("timestamp");


--
-- Name: telematics_events_2025_10_trip_id_idx; Type: INDEX; Schema: public; Owner: insurance_user
--

CREATE INDEX telematics_events_2025_10_trip_id_idx ON public.telematics_events_2025_10 USING btree (trip_id);


--
-- Name: telematics_events_2024_11_driver_id_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_driver_id ATTACH PARTITION public.telematics_events_2024_11_driver_id_idx;


--
-- Name: telematics_events_2024_11_pkey; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.telematics_events_pkey ATTACH PARTITION public.telematics_events_2024_11_pkey;


--
-- Name: telematics_events_2024_11_timestamp_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_timestamp ATTACH PARTITION public.telematics_events_2024_11_timestamp_idx;


--
-- Name: telematics_events_2024_11_trip_id_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_trip_id ATTACH PARTITION public.telematics_events_2024_11_trip_id_idx;


--
-- Name: telematics_events_2024_12_driver_id_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_driver_id ATTACH PARTITION public.telematics_events_2024_12_driver_id_idx;


--
-- Name: telematics_events_2024_12_pkey; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.telematics_events_pkey ATTACH PARTITION public.telematics_events_2024_12_pkey;


--
-- Name: telematics_events_2024_12_timestamp_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_timestamp ATTACH PARTITION public.telematics_events_2024_12_timestamp_idx;


--
-- Name: telematics_events_2024_12_trip_id_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_trip_id ATTACH PARTITION public.telematics_events_2024_12_trip_id_idx;


--
-- Name: telematics_events_2025_01_driver_id_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_driver_id ATTACH PARTITION public.telematics_events_2025_01_driver_id_idx;


--
-- Name: telematics_events_2025_01_pkey; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.telematics_events_pkey ATTACH PARTITION public.telematics_events_2025_01_pkey;


--
-- Name: telematics_events_2025_01_timestamp_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_timestamp ATTACH PARTITION public.telematics_events_2025_01_timestamp_idx;


--
-- Name: telematics_events_2025_01_trip_id_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_trip_id ATTACH PARTITION public.telematics_events_2025_01_trip_id_idx;


--
-- Name: telematics_events_2025_09_driver_id_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_driver_id ATTACH PARTITION public.telematics_events_2025_09_driver_id_idx;


--
-- Name: telematics_events_2025_09_pkey; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.telematics_events_pkey ATTACH PARTITION public.telematics_events_2025_09_pkey;


--
-- Name: telematics_events_2025_09_timestamp_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_timestamp ATTACH PARTITION public.telematics_events_2025_09_timestamp_idx;


--
-- Name: telematics_events_2025_09_trip_id_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_trip_id ATTACH PARTITION public.telematics_events_2025_09_trip_id_idx;


--
-- Name: telematics_events_2025_10_driver_id_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_driver_id ATTACH PARTITION public.telematics_events_2025_10_driver_id_idx;


--
-- Name: telematics_events_2025_10_pkey; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.telematics_events_pkey ATTACH PARTITION public.telematics_events_2025_10_pkey;


--
-- Name: telematics_events_2025_10_timestamp_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_timestamp ATTACH PARTITION public.telematics_events_2025_10_timestamp_idx;


--
-- Name: telematics_events_2025_10_trip_id_idx; Type: INDEX ATTACH; Schema: public; Owner: insurance_user
--

ALTER INDEX public.idx_events_trip_id ATTACH PARTITION public.telematics_events_2025_10_trip_id_idx;


--
-- Name: drivers update_drivers_updated_at; Type: TRIGGER; Schema: public; Owner: insurance_user
--

CREATE TRIGGER update_drivers_updated_at BEFORE UPDATE ON public.drivers FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: premiums update_premiums_updated_at; Type: TRIGGER; Schema: public; Owner: insurance_user
--

CREATE TRIGGER update_premiums_updated_at BEFORE UPDATE ON public.premiums FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: insurance_user
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: vehicles update_vehicles_updated_at; Type: TRIGGER; Schema: public; Owner: insurance_user
--

CREATE TRIGGER update_vehicles_updated_at BEFORE UPDATE ON public.vehicles FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: claims claims_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.claims
    ADD CONSTRAINT claims_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(driver_id);


--
-- Name: devices devices_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(driver_id) ON DELETE CASCADE;


--
-- Name: devices devices_vehicle_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_vehicle_id_fkey FOREIGN KEY (vehicle_id) REFERENCES public.vehicles(vehicle_id) ON DELETE CASCADE;


--
-- Name: driver_statistics driver_statistics_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.driver_statistics
    ADD CONSTRAINT driver_statistics_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(driver_id) ON DELETE CASCADE;


--
-- Name: premiums premiums_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.premiums
    ADD CONSTRAINT premiums_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(driver_id) ON DELETE CASCADE;


--
-- Name: risk_scores risk_scores_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.risk_scores
    ADD CONSTRAINT risk_scores_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(driver_id) ON DELETE CASCADE;


--
-- Name: telematics_events telematics_events_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE public.telematics_events
    ADD CONSTRAINT telematics_events_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(device_id);


--
-- Name: telematics_events telematics_events_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE public.telematics_events
    ADD CONSTRAINT telematics_events_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(driver_id);


--
-- Name: telematics_events telematics_events_trip_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE public.telematics_events
    ADD CONSTRAINT telematics_events_trip_id_fkey FOREIGN KEY (trip_id) REFERENCES public.trips(trip_id);


--
-- Name: trips trips_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(device_id);


--
-- Name: trips trips_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(driver_id) ON DELETE CASCADE;


--
-- Name: users users_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(driver_id);


--
-- Name: vehicles vehicles_driver_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: insurance_user
--

ALTER TABLE ONLY public.vehicles
    ADD CONSTRAINT vehicles_driver_id_fkey FOREIGN KEY (driver_id) REFERENCES public.drivers(driver_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict vU0dT3p9D0HVMmrT8H50Vbfnta08BKuRXVKVBENladnm51MTOkXZGfQKp3nlRDi

