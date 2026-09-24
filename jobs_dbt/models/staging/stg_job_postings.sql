select
    job_id,
    search_term,
    trim(regexp_replace(title, '<[^>]+>', '', 'g'))       as title,
    trim(company)                                          as company,
    location,
    json_extract_string(raw_json, '$.location.area[1]')    as state,
    regexp_replace(description, '<[^>]+>', '', 'g')        as description,
    created_at,
    cast(created_at as date)                               as posted_date,
    salary_min,
    salary_max,
    contract_time,
    redirect_url,
    ingested_at
from {{ source('raw', 'job_postings') }}
