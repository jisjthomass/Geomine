CREATE EXTENSION IF NOT EXISTS postgis;
--
-- PostgreSQL database dump
--



-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

-- Started on 2026-09-02 19:35:07

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 226 (class 1259 OID 18618)
-- Name: historical_drilling_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.historical_drilling_events (
    id integer NOT NULL,
    well_id character varying(50) NOT NULL,
    latitude double precision NOT NULL,
    longitude double precision NOT NULL,
    geom public.geometry(Point,4326),
    event_depth double precision NOT NULL,
    event_type character varying(100) NOT NULL,
    formation character varying(100) NOT NULL,
    summary_text text
);


ALTER TABLE public.historical_drilling_events OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 18617)
-- Name: historical_drilling_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.historical_drilling_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.historical_drilling_events_id_seq OWNER TO postgres;

--
-- TOC entry 5931 (class 0 OID 0)
-- Dependencies: 225
-- Name: historical_drilling_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.historical_drilling_events_id_seq OWNED BY public.historical_drilling_events.id;


--
-- TOC entry 5768 (class 2604 OID 18621)
-- Name: historical_drilling_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historical_drilling_events ALTER COLUMN id SET DEFAULT nextval('public.historical_drilling_events_id_seq'::regclass);


--
-- TOC entry 5925 (class 0 OID 18618)
-- Dependencies: 226
-- Data for Name: historical_drilling_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.historical_drilling_events (id, well_id, latitude, longitude, geom, event_depth, event_type, formation, summary_text) FROM stdin;
100	OIL-DGB-204	27.248096	95.291704	0101000020E610000031074147ABD25740B7442E38833F3B40	2875.8	Shale Instability	Kopili Shale	Encountered Shale Instability in Kopili Shale at depth 2875.8m. Operational parameters adjusted and monitored closely.
1	OIL-MKM-12	27.306947	95.582623	0101000020E61000006FB9FAB149E55740F69A1E14944E3B40	4020.9	Stuck Pipe Incident	Kopili Shale	Encountered Stuck Pipe Incident in Kopili Shale at depth 4020.9m. Operational parameters adjusted and monitored closely.
2	OIL-DGB-204	27.334279	95.557364	0101000020E6100000F0FD0DDAABE3574055BDFC4E93553B40	2530.1	Stuck Pipe Incident	Barail Coal-Shale	Encountered Stuck Pipe Incident in Barail Coal-Shale at depth 2530.1m. Operational parameters adjusted and monitored closely.
3	OIL-DLJ-102	27.470492	95.372376	0101000020E61000002E742502D5D757409607E92972783B40	3041	Severe Mud Loss	Lakadong-Therria	Encountered Severe Mud Loss in Lakadong-Therria at depth 3041m. Operational parameters adjusted and monitored closely.
4	OIL-JRJ-88	27.248473	95.273764	0101000020E61000009EB4705985D1574063F030ED9B3F3B40	2755.7	Gas Kick	Lakadong-Therria	Encountered Gas Kick in Lakadong-Therria at depth 2755.7m. Operational parameters adjusted and monitored closely.
5	OIL-MKM-12	27.215108	95.298499	0101000020E6100000E1B88C9B1AD35740A41B615111373B40	2344.9	Severe Mud Loss	Girujan Clay	Encountered Severe Mud Loss in Girujan Clay at depth 2344.9m. Operational parameters adjusted and monitored closely.
6	OIL-DLJ-102	27.213491	95.587606	0101000020E6100000BC3B32569BE5574087FD9E58A7363B40	1944.9	High Torque	Kopili Shale	Encountered High Torque in Kopili Shale at depth 1944.9m. Operational parameters adjusted and monitored closely.
7	OIL-MRN-52	27.308517	95.297984	0101000020E6100000CDAE7B2B12D35740914259F8FA4E3B40	2249.6	High Torque	Kopili Shale	Encountered High Torque in Kopili Shale at depth 2249.6m. Operational parameters adjusted and monitored closely.
8	OIL-MRN-45	27.402603	95.414029	0101000020E61000001EA67D737FDA574080457EFD10673B40	1339.5	Severe Mud Loss	Girujan Clay	Encountered Severe Mud Loss in Girujan Clay at depth 1339.5m. Operational parameters adjusted and monitored closely.
9	OIL-MKM-12	27.34647	95.227621	0101000020E610000080B8AB5791CE57408D0B0742B2583B40	4402.3	Shale Instability	Kopili Shale	Encountered Shale Instability in Kopili Shale at depth 4402.3m. Operational parameters adjusted and monitored closely.
10	OIL-DGB-204	27.444874	95.342928	0101000020E61000007E384888F2D5574038D73043E3713B40	3865.7	Stuck Pipe Incident	Barail Coal-Shale	Encountered Stuck Pipe Incident in Barail Coal-Shale at depth 3865.7m. Operational parameters adjusted and monitored closely.
11	OIL-MRN-52	27.301138	95.22988	0101000020E610000049809A5AB6CE574036954561174D3B40	1291.4	Gas Kick	Barail Coal-Shale	Encountered Gas Kick in Barail Coal-Shale at depth 1291.4m. Operational parameters adjusted and monitored closely.
12	OIL-DLJ-105	27.233204	95.235011	0101000020E6100000D1CC936B0ACF5740E04BE141B33B3B40	3785.7	Stuck Pipe Incident	Kopili Shale	Encountered Stuck Pipe Incident in Kopili Shale at depth 3785.7m. Operational parameters adjusted and monitored closely.
13	OIL-DLJ-105	27.354284	95.413269	0101000020E6100000D7DCD1FF72DA5740FE7E315BB25A3B40	4475	Severe Mud Loss	Kopili Shale	Encountered Severe Mud Loss in Kopili Shale at depth 4475m. Operational parameters adjusted and monitored closely.
14	OIL-MKM-12	27.236617	95.526017	0101000020E6100000F6083543AAE1574079AD84EE923C3B40	1980.6	Shale Instability	Kopili Shale	Encountered Shale Instability in Kopili Shale at depth 1980.6m. Operational parameters adjusted and monitored closely.
15	OIL-MKM-12	27.449452	95.512153	0101000020E61000001763601DC7E057402E1F49490F733B40	4072.4	Gas Kick	Kopili Shale	Encountered Gas Kick in Kopili Shale at depth 4072.4m. Operational parameters adjusted and monitored closely.
16	OIL-DLJ-102	27.234204	95.398543	0101000020E61000002FC37FBA81D95740A69718CBF43B3B40	4245.6	Severe Mud Loss	Girujan Clay	Encountered Severe Mud Loss in Girujan Clay at depth 4245.6m. Operational parameters adjusted and monitored closely.
17	OIL-JRJ-88	27.203854	95.465606	0101000020E610000091B41B7DCCDD5740A62897C62F343B40	2557.9	Normal Operation	Barail Coal-Shale	Standard parameters maintained in Barail Coal-Shale at 2557.9m.
18	OIL-MKM-12	27.495619	95.491586	0101000020E6100000F94A202576DF5740B74604E3E07E3B40	1832.8	Normal Operation	Tipam Sandstone	Standard parameters maintained in Tipam Sandstone at 1832.8m.
19	OIL-DLJ-102	27.286706	95.305689	0101000020E6100000CE6F986890D3574025917D9065493B40	3533.6	Stuck Pipe Incident	Lakadong-Therria	Encountered Stuck Pipe Incident in Lakadong-Therria at depth 3533.6m. Operational parameters adjusted and monitored closely.
20	OIL-MRN-45	27.396977	95.231586	0101000020E6100000880D164ED2CE5740A243E048A0653B40	3648.1	Shale Instability	Barail Coal-Shale	Encountered Shale Instability in Barail Coal-Shale at depth 3648.1m. Operational parameters adjusted and monitored closely.
21	OIL-DLJ-105	27.248038	95.335303	0101000020E61000000BD0B69A75D557404E2A1A6B7F3F3B40	2079.7	Normal Operation	Lakadong-Therria	Standard parameters maintained in Lakadong-Therria at 2079.7m.
22	OIL-DLJ-102	27.352595	95.248085	0101000020E61000003468E89FE0CF5740AEBB79AA435A3B40	4055.7	Shale Instability	Tipam Sandstone	Encountered Shale Instability in Tipam Sandstone at depth 4055.7m. Operational parameters adjusted and monitored closely.
23	OIL-DGB-204	27.399404	95.392209	0101000020E6100000990CC7F319D957403FE42D573F663B40	3705.2	High Torque	Tipam Sandstone	Encountered High Torque in Tipam Sandstone at depth 3705.2m. Operational parameters adjusted and monitored closely.
24	OIL-MKM-12	27.35552	95.523604	0101000020E610000082035ABA82E15740EC12D55B035B3B40	4218.9	Normal Operation	Tipam Sandstone	Standard parameters maintained in Tipam Sandstone at 4218.9m.
25	OIL-MRN-45	27.296233	95.39882	0101000020E6100000683F524486D95740F8FE06EDD54B3B40	2752	Gas Kick	Kopili Shale	Encountered Gas Kick in Kopili Shale at depth 2752m. Operational parameters adjusted and monitored closely.
26	OIL-MRN-52	27.426701	95.387949	0101000020E610000005E10A28D4D85740A62BD8463C6D3B40	3813.1	Gas Kick	Kopili Shale	Encountered Gas Kick in Kopili Shale at depth 3813.1m. Operational parameters adjusted and monitored closely.
27	OIL-DLJ-102	27.209101	95.308948	0101000020E6100000890AD5CDC5D35740978FA4A487353B40	1403.3	Stuck Pipe Incident	Barail Coal-Shale	Encountered Stuck Pipe Incident in Barail Coal-Shale at depth 1403.3m. Operational parameters adjusted and monitored closely.
28	OIL-JRJ-88	27.448046	95.389731	0101000020E610000031CF4A5AF1D85740871A8524B3723B40	1834.6	Normal Operation	Kopili Shale	Standard parameters maintained in Kopili Shale at 1834.6m.
29	OIL-MRN-45	27.220234	95.338009	0101000020E61000003C3080F0A1D557409F77634161383B40	3920.6	High Torque	Lakadong-Therria	Encountered High Torque in Lakadong-Therria at depth 3920.6m. Operational parameters adjusted and monitored closely.
30	OIL-DLJ-105	27.220676	95.476327	0101000020E6100000EACC3D247CDE57401903EB387E383B40	3554.9	High Torque	Lakadong-Therria	Encountered High Torque in Lakadong-Therria at depth 3554.9m. Operational parameters adjusted and monitored closely.
31	OIL-MRN-45	27.448051	95.290395	0101000020E610000001FBE8D495D25740AAF06778B3723B40	2272.4	Shale Instability	Lakadong-Therria	Encountered Shale Instability in Lakadong-Therria at depth 2272.4m. Operational parameters adjusted and monitored closely.
32	OIL-MRN-45	27.21623	95.220911	0101000020E6100000E814E46723CE5740016A6AD95A373B40	3879.9	Shale Instability	Girujan Clay	Encountered Shale Instability in Girujan Clay at depth 3879.9m. Operational parameters adjusted and monitored closely.
33	OIL-DLJ-105	27.359078	95.481161	0101000020E610000015C78157CBDE57408DB62A89EC5B3B40	2544.9	High Torque	Tipam Sandstone	Encountered High Torque in Tipam Sandstone at depth 2544.9m. Operational parameters adjusted and monitored closely.
34	OIL-DGB-204	27.268954	95.478939	0101000020E6100000DA71C3EFA6DE5740DE205A2BDA443B40	4494.7	Shale Instability	Girujan Clay	Encountered Shale Instability in Girujan Clay at depth 4494.7m. Operational parameters adjusted and monitored closely.
35	OIL-MRN-52	27.342661	95.279013	0101000020E61000002B8A5759DBD157405A9D9CA1B8573B40	1782.7	Shale Instability	Girujan Clay	Encountered Shale Instability in Girujan Clay at depth 1782.7m. Operational parameters adjusted and monitored closely.
36	OIL-DLJ-105	27.248056	95.539328	0101000020E61000004B74965984E257409A931799803F3B40	2109.6	Stuck Pipe Incident	Lakadong-Therria	Encountered Stuck Pipe Incident in Lakadong-Therria at depth 2109.6m. Operational parameters adjusted and monitored closely.
37	OIL-DGB-204	27.497278	95.438053	0101000020E61000008A3A730F09DC574032056B9C4D7F3B40	3540.9	Shale Instability	Kopili Shale	Encountered Shale Instability in Kopili Shale at depth 3540.9m. Operational parameters adjusted and monitored closely.
38	OIL-DGB-204	27.224437	95.377062	0101000020E61000001EA4A7C821D857402A0307B474393B40	4410.3	Stuck Pipe Incident	Girujan Clay	Encountered Stuck Pipe Incident in Girujan Clay at depth 4410.3m. Operational parameters adjusted and monitored closely.
39	OIL-JRJ-88	27.363327	95.356993	0101000020E6100000A9F92AF9D8D65740F9C08EFF025D3B40	3250.5	Gas Kick	Barail Coal-Shale	Encountered Gas Kick in Barail Coal-Shale at depth 3250.5m. Operational parameters adjusted and monitored closely.
40	OIL-MRN-45	27.373447	95.298823	0101000020E6100000BA1281EA1FD3574010CAFB389A5F3B40	2691.4	Gas Kick	Barail Coal-Shale	Encountered Gas Kick in Barail Coal-Shale at depth 2691.4m. Operational parameters adjusted and monitored closely.
41	OIL-JRJ-88	27.35895	95.524262	0101000020E6100000462234828DE1574032E6AE25E45B3B40	3566.2	Severe Mud Loss	Barail Coal-Shale	Encountered Severe Mud Loss in Barail Coal-Shale at depth 3566.2m. Operational parameters adjusted and monitored closely.
42	OIL-MRN-52	27.323525	95.420438	0101000020E6100000B9FFC874E8DA57403B70CE88D2523B40	4045.8	Gas Kick	Lakadong-Therria	Encountered Gas Kick in Lakadong-Therria at depth 4045.8m. Operational parameters adjusted and monitored closely.
43	OIL-DLJ-105	27.301789	95.458474	0101000020E61000003E0455A357DD5740E44A3D0B424D3B40	3632.1	Severe Mud Loss	Lakadong-Therria	Encountered Severe Mud Loss in Lakadong-Therria at depth 3632.1m. Operational parameters adjusted and monitored closely.
44	OIL-DLJ-105	27.343491	95.450028	0101000020E610000032923D42CDDC57406878B306EF573B40	3374.1	Gas Kick	Kopili Shale	Encountered Gas Kick in Kopili Shale at depth 3374.1m. Operational parameters adjusted and monitored closely.
45	OIL-MRN-45	27.317015	95.512717	0101000020E61000009BC6F65AD0E05740695721E527513B40	4046.4	Normal Operation	Lakadong-Therria	Standard parameters maintained in Lakadong-Therria at 4046.4m.
46	OIL-DGB-204	27.227964	95.327731	0101000020E6100000AAB8718BF9D4574054AA44D95B3A3B40	4425.1	Severe Mud Loss	Kopili Shale	Encountered Severe Mud Loss in Kopili Shale at depth 4425.1m. Operational parameters adjusted and monitored closely.
47	OIL-JRJ-88	27.403473	95.324924	0101000020E6100000DF6B088ECBD45740ABD1AB014A673B40	3997.2	Gas Kick	Barail Coal-Shale	Encountered Gas Kick in Barail Coal-Shale at depth 3997.2m. Operational parameters adjusted and monitored closely.
48	OIL-MRN-52	27.492081	95.32201	0101000020E61000000ABFD4CF9BD45740A4FB3905F97D3B40	2940.7	Normal Operation	Kopili Shale	Standard parameters maintained in Kopili Shale at 2940.7m.
49	OIL-MRN-45	27.457747	95.319726	0101000020E6100000946B0A6476D4574095D74AE82E753B40	3702.6	Normal Operation	Girujan Clay	Standard parameters maintained in Girujan Clay at 3702.6m.
50	OIL-DGB-204	27.348234	95.580134	0101000020E61000000D535BEA20E55740F35A09DD25593B40	2928.4	Gas Kick	Girujan Clay	Encountered Gas Kick in Girujan Clay at depth 2928.4m. Operational parameters adjusted and monitored closely.
51	OIL-MKM-12	27.379881	95.490884	0101000020E61000004C88B9A46ADF57402D5F97E13F613B40	3543.4	Severe Mud Loss	Tipam Sandstone	Encountered Severe Mud Loss in Tipam Sandstone at depth 3543.4m. Operational parameters adjusted and monitored closely.
52	OIL-DGB-204	27.470564	95.304439	0101000020E61000002028B7ED7BD35740C9ACDEE176783B40	3343.6	Severe Mud Loss	Tipam Sandstone	Encountered Severe Mud Loss in Tipam Sandstone at depth 3343.6m. Operational parameters adjusted and monitored closely.
53	OIL-MRN-52	27.352913	95.523679	0101000020E610000087A6ECF483E157405055A181585A3B40	4428.2	Gas Kick	Kopili Shale	Encountered Gas Kick in Kopili Shale at depth 4428.2m. Operational parameters adjusted and monitored closely.
54	OIL-DLJ-105	27.277419	95.474688	0101000020E61000006FF3C64961DE5740FD497CEE04473B40	2751.3	Gas Kick	Kopili Shale	Encountered Gas Kick in Kopili Shale at depth 2751.3m. Operational parameters adjusted and monitored closely.
55	OIL-DLJ-102	27.426605	95.229316	0101000020E6100000C51C041DADCE5740614F3BFC356D3B40	4029.4	Severe Mud Loss	Lakadong-Therria	Encountered Severe Mud Loss in Lakadong-Therria at depth 4029.4m. Operational parameters adjusted and monitored closely.
56	OIL-MRN-52	27.269148	95.571132	0101000020E6100000BE6C3B6D8DE45740A8C821E2E6443B40	3447.3	Gas Kick	Kopili Shale	Encountered Gas Kick in Kopili Shale at depth 3447.3m. Operational parameters adjusted and monitored closely.
57	OIL-JRJ-88	27.348981	95.453499	0101000020E61000003271AB2006DD5740E5EC9DD156593B40	4417.2	Stuck Pipe Incident	Lakadong-Therria	Encountered Stuck Pipe Incident in Lakadong-Therria at depth 4417.2m. Operational parameters adjusted and monitored closely.
58	OIL-DLJ-102	27.455509	95.333602	0101000020E610000055F833BC59D557409E08E23C9C743B40	1820.2	Gas Kick	Lakadong-Therria	Encountered Gas Kick in Lakadong-Therria at depth 1820.2m. Operational parameters adjusted and monitored closely.
59	OIL-DLJ-105	27.405079	95.452872	0101000020E61000008B51D7DAFBDC5740E04BE141B3673B40	3862.8	Shale Instability	Girujan Clay	Encountered Shale Instability in Girujan Clay at depth 3862.8m. Operational parameters adjusted and monitored closely.
60	OIL-MRN-52	27.246361	95.519407	0101000020E61000001094DBF63DE157408602B683113F3B40	4035.8	Shale Instability	Lakadong-Therria	Encountered Shale Instability in Lakadong-Therria at depth 4035.8m. Operational parameters adjusted and monitored closely.
61	OIL-MRN-52	27.39214	95.205795	0101000020E61000008AABCABE2BCD574015747B4963643B40	1653.4	Severe Mud Loss	Kopili Shale	Encountered Severe Mud Loss in Kopili Shale at depth 1653.4m. Operational parameters adjusted and monitored closely.
62	OIL-DGB-204	27.481756	95.520489	0101000020E6100000603B18B14FE15740DBA6785C547B3B40	3779.7	Gas Kick	Tipam Sandstone	Encountered Gas Kick in Tipam Sandstone at depth 3779.7m. Operational parameters adjusted and monitored closely.
63	OIL-JRJ-88	27.466311	95.450788	0101000020E6100000795BE9B5D9DC5740DBC35E2860773B40	2359.1	Stuck Pipe Incident	Barail Coal-Shale	Encountered Stuck Pipe Incident in Barail Coal-Shale at depth 2359.1m. Operational parameters adjusted and monitored closely.
64	OIL-MRN-52	27.407011	95.405589	0101000020E610000083A7902BF5D95740BD1C76DF31683B40	1964.6	Normal Operation	Kopili Shale	Standard parameters maintained in Kopili Shale at 1964.6m.
65	OIL-MRN-52	27.369251	95.332613	0101000020E61000005D4E098849D55740EA03C93B875E3B40	4049.1	Severe Mud Loss	Lakadong-Therria	Encountered Severe Mud Loss in Lakadong-Therria at depth 4049.1m. Operational parameters adjusted and monitored closely.
66	OIL-MKM-12	27.205536	95.439516	0101000020E61000006684B70721DC57409126DE019E343B40	2675.9	Gas Kick	Barail Coal-Shale	Encountered Gas Kick in Barail Coal-Shale at depth 2675.9m. Operational parameters adjusted and monitored closely.
67	OIL-JRJ-88	27.3864	95.441726	0101000020E6100000BFF2203D45DC5740A52C431CEB623B40	2396.5	High Torque	Tipam Sandstone	Encountered High Torque in Tipam Sandstone at depth 2396.5m. Operational parameters adjusted and monitored closely.
68	OIL-DGB-204	27.343165	95.565594	0101000020E610000016342DB132E45740C02154A9D9573B40	4242.6	Gas Kick	Tipam Sandstone	Encountered Gas Kick in Tipam Sandstone at depth 4242.6m. Operational parameters adjusted and monitored closely.
69	OIL-MKM-12	27.38785	95.469707	0101000020E6100000F2ECF2AD0FDE5740ECC039234A633B40	2768.3	Normal Operation	Kopili Shale	Standard parameters maintained in Kopili Shale at 2768.3m.
70	OIL-MKM-12	27.315565	95.281754	0101000020E61000001AE1ED4108D2574022C32ADEC8503B40	2580.6	Severe Mud Loss	Tipam Sandstone	Encountered Severe Mud Loss in Tipam Sandstone at depth 2580.6m. Operational parameters adjusted and monitored closely.
71	OIL-MKM-12	27.351927	95.342559	0101000020E6100000D47C957CECD5574053944BE3175A3B40	3532.5	Normal Operation	Girujan Clay	Standard parameters maintained in Girujan Clay at 3532.5m.
72	OIL-MRN-52	27.259556	95.527748	0101000020E6100000E2218C9FC6E15740077B134372423B40	3479.2	Gas Kick	Girujan Clay	Encountered Gas Kick in Girujan Clay at depth 3479.2m. Operational parameters adjusted and monitored closely.
73	OIL-MKM-12	27.250814	95.307681	0101000020E61000007026A60BB1D357400261A75835403B40	3635.7	Shale Instability	Kopili Shale	Encountered Shale Instability in Kopili Shale at depth 3635.7m. Operational parameters adjusted and monitored closely.
74	OIL-MKM-12	27.291329	95.588364	0101000020E610000033897AC1A7E557405B608F89944A3B40	1228.3	Shale Instability	Girujan Clay	Encountered Shale Instability in Girujan Clay at depth 1228.3m. Operational parameters adjusted and monitored closely.
75	OIL-DGB-204	27.399036	95.487736	0101000020E61000003D450E1137DF574039ED293927663B40	3103.6	Gas Kick	Girujan Clay	Encountered Gas Kick in Girujan Clay at depth 3103.6m. Operational parameters adjusted and monitored closely.
76	OIL-MKM-12	27.213822	95.243426	0101000020E6100000C03FA54A94CF5740522AE109BD363B40	3487.9	Stuck Pipe Incident	Kopili Shale	Encountered Stuck Pipe Incident in Kopili Shale at depth 3487.9m. Operational parameters adjusted and monitored closely.
77	OIL-DLJ-105	27.433801	95.559035	0101000020E61000007094BC3AC7E35740DBF813950D6F3B40	2337.8	Gas Kick	Kopili Shale	Encountered Gas Kick in Kopili Shale at depth 2337.8m. Operational parameters adjusted and monitored closely.
78	OIL-MKM-12	27.454646	95.536573	0101000020E6100000AABA473657E25740D94125AE63743B40	2540.2	Normal Operation	Lakadong-Therria	Standard parameters maintained in Lakadong-Therria at 2540.2m.
79	OIL-DLJ-105	27.377354	95.560804	0101000020E6100000D3DD7536E4E35740C90391459A603B40	2007.6	Shale Instability	Tipam Sandstone	Encountered Shale Instability in Tipam Sandstone at depth 2007.6m. Operational parameters adjusted and monitored closely.
80	OIL-DLJ-105	27.473553	95.312699	0101000020E61000007B9FAA4203D4574035ECF7C43A793B40	2686.5	Gas Kick	Kopili Shale	Encountered Gas Kick in Kopili Shale at depth 2686.5m. Operational parameters adjusted and monitored closely.
81	OIL-DLJ-105	27.438566	95.571261	0101000020E6100000BD1E4C8A8FE45740362383DC45703B40	3831.1	Normal Operation	Tipam Sandstone	Standard parameters maintained in Tipam Sandstone at 3831.1m.
82	OIL-MRN-45	27.228618	95.37849	0101000020E61000003CF71E2E39D85740E54691B5863A3B40	2868	High Torque	Kopili Shale	Encountered High Torque in Kopili Shale at depth 2868m. Operational parameters adjusted and monitored closely.
83	OIL-MKM-12	27.278008	95.398883	0101000020E61000008BFB8F4C87D95740C00644882B473B40	1270.7	High Torque	Barail Coal-Shale	Encountered High Torque in Barail Coal-Shale at depth 1270.7m. Operational parameters adjusted and monitored closely.
84	OIL-DGB-204	27.469541	95.351891	0101000020E61000006E30D46185D657409221C7D633783B40	4277.2	Severe Mud Loss	Girujan Clay	Encountered Severe Mud Loss in Girujan Clay at depth 4277.2m. Operational parameters adjusted and monitored closely.
85	OIL-MRN-45	27.420782	95.332957	0101000020E61000005A7EE02A4FD55740D7BE805EB86B3B40	1385.4	Stuck Pipe Incident	Kopili Shale	Encountered Stuck Pipe Incident in Kopili Shale at depth 1385.4m. Operational parameters adjusted and monitored closely.
86	OIL-DGB-204	27.31268	95.53927	0101000020E6100000B16D516683E25740001DE6CB0B503B40	3134.2	Shale Instability	Barail Coal-Shale	Encountered Shale Instability in Barail Coal-Shale at depth 3134.2m. Operational parameters adjusted and monitored closely.
87	OIL-DLJ-102	27.429166	95.364106	0101000020E6100000C19140834DD757401D8EAED2DD6D3B40	2914.2	Shale Instability	Girujan Clay	Encountered Shale Instability in Girujan Clay at depth 2914.2m. Operational parameters adjusted and monitored closely.
88	OIL-MKM-12	27.234382	95.528023	0101000020E61000004B22FB20CBE1574065C57075003C3B40	2061.4	Gas Kick	Lakadong-Therria	Encountered Gas Kick in Lakadong-Therria at depth 2061.4m. Operational parameters adjusted and monitored closely.
89	OIL-JRJ-88	27.400484	95.493304	0101000020E61000001ABFF04A92DF57403E92921E86663B40	2967.3	Gas Kick	Tipam Sandstone	Encountered Gas Kick in Tipam Sandstone at depth 2967.3m. Operational parameters adjusted and monitored closely.
90	OIL-DLJ-102	27.233825	95.530501	0101000020E6100000B35F77BAF3E15740B9FC87F4DB3B3B40	1768.8	Stuck Pipe Incident	Kopili Shale	Encountered Stuck Pipe Incident in Kopili Shale at depth 1768.8m. Operational parameters adjusted and monitored closely.
91	OIL-DGB-204	27.343087	95.504027	0101000020E6100000435376FA41E05740C9AEB48CD4573B40	2977.6	Stuck Pipe Incident	Tipam Sandstone	Encountered Stuck Pipe Incident in Tipam Sandstone at depth 2977.6m. Operational parameters adjusted and monitored closely.
92	OIL-MRN-52	27.47483	95.380772	0101000020E6100000E1CE85915ED85740E12879758E793B40	3012.1	Gas Kick	Lakadong-Therria	Encountered Gas Kick in Lakadong-Therria at depth 3012.1m. Operational parameters adjusted and monitored closely.
93	OIL-MKM-12	27.200156	95.21432	0101000020E61000003DB83B6BB7CD57402219726C3D333B40	3896.5	Severe Mud Loss	Lakadong-Therria	Encountered Severe Mud Loss in Lakadong-Therria at depth 3896.5m. Operational parameters adjusted and monitored closely.
94	OIL-MRN-45	27.374862	95.561027	0101000020E6100000124BCADDE7E357405E83BEF4F65F3B40	4006.1	Gas Kick	Lakadong-Therria	Encountered Gas Kick in Lakadong-Therria at depth 4006.1m. Operational parameters adjusted and monitored closely.
95	OIL-JRJ-88	27.208608	95.358443	0101000020E6100000BA9EE8BAF0D6574019AF795567353B40	3024.7	Stuck Pipe Incident	Girujan Clay	Encountered Stuck Pipe Incident in Girujan Clay at depth 3024.7m. Operational parameters adjusted and monitored closely.
96	OIL-MRN-45	27.373242	95.338103	0101000020E61000007DEBC37AA3D557405F7EA7C98C5F3B40	3389.7	Severe Mud Loss	Kopili Shale	Encountered Severe Mud Loss in Kopili Shale at depth 3389.7m. Operational parameters adjusted and monitored closely.
97	OIL-DLJ-102	27.401636	95.216044	0101000020E6100000CF9F36AAD3CD574071E5EC9DD1663B40	3691.9	High Torque	Barail Coal-Shale	Encountered High Torque in Barail Coal-Shale at depth 3691.9m. Operational parameters adjusted and monitored closely.
98	OIL-JRJ-88	27.492498	95.310439	0101000020E6100000CA198A3BDED357406D585359147E3B40	4204.6	Gas Kick	Kopili Shale	Encountered Gas Kick in Kopili Shale at depth 4204.6m. Operational parameters adjusted and monitored closely.
99	OIL-DGB-204	27.446955	95.578122	0101000020E610000047C66AF3FFE457409FC893A46B723B40	1488	Normal Operation	Barail Coal-Shale	Standard parameters maintained in Barail Coal-Shale at 1488m.
\.


--
-- TOC entry 5932 (class 0 OID 0)
-- Dependencies: 225
-- Name: historical_drilling_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.historical_drilling_events_id_seq', 100, true);


--
-- TOC entry 5770 (class 2606 OID 18632)
-- Name: historical_drilling_events historical_drilling_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.historical_drilling_events
    ADD CONSTRAINT historical_drilling_events_pkey PRIMARY KEY (id);


--
-- TOC entry 5771 (class 2620 OID 18633)
-- Name: historical_drilling_events trg_historical_drilling_geom; Type: TRIGGER; Schema: public; Owner: postgres
--

-- DISABLED: CREATE TRIGGER trg_historical_drilling_geom BEFORE INSERT OR UPDATE ON public.historical_drilling_events FOR EACH ROW EXECUTE FUNCTION public.update_historical_drilling_geom();


-- Completed on 2026-09-02 19:35:08

--
-- PostgreSQL database dump complete
--



-- ============================================================
-- Round 2 Schema Upgrades (appended to guarantee execution)
-- These columns are queried by data_loader.py
-- ============================================================
ALTER TABLE public.historical_drilling_events ADD COLUMN IF NOT EXISTS cause TEXT DEFAULT '';
ALTER TABLE public.historical_drilling_events ADD COLUMN IF NOT EXISTS mitigation TEXT DEFAULT '';
ALTER TABLE public.historical_drilling_events ADD COLUMN IF NOT EXISTS outcome TEXT DEFAULT '';
ALTER TABLE public.historical_drilling_events ADD COLUMN IF NOT EXISTS npt_duration_minutes INT DEFAULT 0;
ALTER TABLE public.historical_drilling_events ADD COLUMN IF NOT EXISTS npt_category VARCHAR(50) DEFAULT 'Unknown';
