-- Staging model: tisztított nyers adatok a Staging_Movies táblából
WITH source AS (
    SELECT
        staging_id,
        movie_id,
        title,
        genres,
        original_language,
        overview,
        popularity,
        production_companies,
        release_date,
        budget,
        revenue,
        runtime,
        vote_average,
        vote_count,
        profit,
        roi,
        release_year,
        release_month,
        source,
        load_date
    FROM dbo.Staging_Movies
    WHERE movie_id IS NOT NULL
      AND title IS NOT NULL
      AND title != ''
      AND budget > 0
      AND revenue > 0
),

cleaned AS (
    SELECT
        movie_id,
        title,
        genres,
        original_language,
        COALESCE(overview, '')           AS overview,
        COALESCE(popularity, 0)          AS popularity,
        production_companies,
        release_date,
        budget,
        revenue,
        COALESCE(runtime, 0)             AS runtime,
        COALESCE(vote_average, 0)        AS vote_average,
        COALESCE(vote_count, 0)          AS vote_count,
        revenue - budget                 AS profit,
        (revenue - budget) / budget      AS roi,
        release_year,
        release_month,
        source,
        load_date
    FROM source
)

SELECT * FROM cleaned