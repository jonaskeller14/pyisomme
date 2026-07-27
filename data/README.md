# data - References

Directory tree:
- [iso-mme-org](iso-mme-org) 
  - [MME 1.6 Testdata short](iso-mme-org/MME%201.6%20Testdata%20short) [[Download](https://www.iso-mme.org/forum/download/file.php?id=582)]
    - [98_7707](iso-mme-org/MME%201.6%20Testdata%20short/98_7707)
    - [3239](iso-mme-org/MME%201.6%20Testdata%20short/3239)
    - [AK3T02FO](iso-mme-org/MME%201.6%20Testdata%20short/AK3T02FO)
    - [AK3T02SI](iso-mme-org/MME%201.6%20Testdata%20short/AK3T02SI)
    - [VW1FGS15](iso-mme-org/MME%201.6%20Testdata%20short/VW1FGS15)
- [nhtsa](nhtsa) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle)]
  - [09203](nhtsa/09203) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases/#/vehicle/9203), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v00000/v09200/v09203ISO.zip)]
    - Fixed via [fix_channel_metadata.py](nhtsa/09203/fix_channel_metadata.py):
      chest displacement unit corrected from m to μm; dummy field set to TH (THOR, test object 2 / position 1, code 21) and H3 (Hybrid III, position 4, code 24)
  - [11391](nhtsa/11391) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/11391), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v11300/v11391ISO.zip)]
  - [14065](nhtsa/14065) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/14065), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v14000/v14065ISO.zip)]
  - [14084](nhtsa/14084) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/14084), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v14000/v14084ISO.zip)]
    - Fixed via [fix_channel_metadata.py](nhtsa/14084/fix_channel_metadata.py):
      chest displacement unit corrected from m to μm; dummy field set to H3 (driver, code 11) and HF (passenger, code 13)


  - [v09203ISO.zip](nhtsa/v09203ISO.zip) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases/#/vehicle/9203), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v00000/v09200/v09203ISO.zip)]
  - [v11391ISO.zip](nhtsa/v11391ISO.zip) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/11391), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v11300/v11391ISO.zip)]
  - [v14065ISO.zip](nhtsa/v14065ISO.zip) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/14065), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v14000/v14065ISO.zip)]
  - [v14084ISO.zip](nhtsa/v14084ISO.zip) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/14084), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v14000/v14084ISO.zip)]
  - [v15036ISO.zip](nhtsa/v15036ISO.zip) [[Source](https://www.nhtsa.gov/research-data/research-testing-databases#/vehicle/15036), [Download](https://nrd-static.nhtsa.dot.gov/compress/iso/vehdb/v10000/v15000/v15036ISO.zip)] — read directly as a zip by `tests/test_report.py`
