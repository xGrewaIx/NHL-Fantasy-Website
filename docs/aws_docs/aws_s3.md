# AWS S3 data storage 

## S3 Architecture 
```text
                    NHL API
                       |
                       v
               Python Ingestion
                       |
                       v
              +----------------+
              |  S3 BRONZE     |
              |  Raw API Data  |
              +----------------+
                       |
                       v
            Clean and Process Data     
                       |
                       v
              +----------------+
              |  S3 SILVER     |
              | Cleaned Data   |
              +----------------+
                       |
                       v
            Get data ready for website/analytics
                       |
                       v
              +----------------+
              |   S3 GOLD      |
              | Analytics Data |
              +----------------+
                       | 
                       v
```

- Each data layer uses a separate S3 bucket.


## Bronze Layer

Purpose is to store raw NHL API responses with no changes 

Object key structure example: /source={}/entity={}/....... further and further key filters

Using the above strucure makes it easier to obtain/track certain data

## Silver Layer

Purpose of this layer is to clean and standarize all data from the bronze layer

Hande:
- Missing values
- Consistent data types
- etc

## Gold Layer

Purpose is to contain datasets that are ready for the website/analytics

## Security

- Using IAM to access buckets
- All buckets are private


## S3 verioning

S3 versioning is enabledd. This means that each object will have its unique object ID

If accidently a change is made, file is overwritten/deleted we can access the previous version of it