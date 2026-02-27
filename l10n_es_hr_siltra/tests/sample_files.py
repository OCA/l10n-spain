SILTRA_HEADER = "ETIFIE41WS90 00353468        {file_date}        FIE                  "
SILTRA_FOOTER = "ETFFIE41WS90 00353468        {file_date}        FIENS0001300000105   "
SILTRA_COMPANY = """EMP{company_ssid}
RZS  MY COMPANY NAME"""
SILTRA_EMPLOYEE = """TRA{employee_ssid}000000000000000000
AYNSURNAME01           SURNAME02           MAIN_NAME
DAF2023110100000000                                                   """
SILTRA_DIT = """DIT333{start_date}{recaida}{process_start_date}{previous_process_end_date}000000000000  00000000000000000{end_date}00   000
IT2{next_date}  000000000000000000000000000000  0000000000000000         """  # noqa: E501
SILTRA_CIT = "CIT000000000000000000{next_date}                                         "
SILTRA_DIP = (
    "DIP00000000{date}000000000000000000000000000000000000000000000000N00000000 "
)
SILTRA_JUB = (
    "JUB00{date}000000000000000000000000000000000000000000000000000000000000000 "
)
SILTRA_NAC = "NAC{date}                                                           "
