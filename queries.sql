-- 1) Bütün təhlükəli asteroidlər
SELECT name, date, diameter_m, distance_km
FROM asteroids
WHERE hazardous = 1
ORDER BY date;

-- 2) Yerə 1 milyon km-dən yaxın keçənlər
SELECT name, date, distance_km
FROM asteroids
WHERE distance_km < 1000000
ORDER BY distance_km;

-- 3) Hər gün neçə asteroid
SELECT date, COUNT(*) AS say
FROM asteroids
GROUP BY date
ORDER BY date;
