ERA5 z500 / tcwv / lcc, 2004-2021, 6-hourly (00/06/12/18 UTC)
Area [N, W, S, E] = [60, -30, 45, 5], 0.25 deg native grid (61 lat x 141 lon)
Source: Copernicus Climate Change Service (C3S) Climate Data Store, ERA5 reanalysis
Values are exactly as delivered by CDS (no interpolation, unit conversion or filling).
number/expver/pressure_level coordinates dropped; z renamed to z500.

04-21_z500.nc
  variable: z500 (Geopotential), units: m**2 s**-2
  dims: valid_time=26300 x latitude=61 (60.0..45.0) x longitude=141 (-30.0..5.0)
  min=46468 max=58810.5 mean=54535.4
  check: z500: OK steps=26300 6h_regular=True 2004-01-01 00:00..2021-12-31 18:00 grid=61x141 NaN=0 values_identical_to_chunks=True
  sha256: b2a2a26a1fc2a80143c514896a2f9f66191c973538e1ff0b18bf216347646b94

04-21_tcwv.nc
  variable: tcwv (Total column vertically-integrated water vapour), units: kg m**-2
  dims: valid_time=26300 x latitude=61 (60.0..45.0) x longitude=141 (-30.0..5.0)
  min=0.963929 max=57.6016 mean=16.4736
  check: tcwv: OK steps=26300 6h_regular=True 2004-01-01 00:00..2021-12-31 18:00 grid=61x141 NaN=0 values_identical_to_chunks=True
  sha256: cd96a723fbfb0bc5de15d2bcc03aa7c73d0a153848b662d98356bb08e0b7f286

04-21_lcc.nc
  variable: lcc (Low cloud cover), units: (0 - 1)
  dims: valid_time=26300 x latitude=61 (60.0..45.0) x longitude=141 (-30.0..5.0)
  min=0 max=1 mean=0.504829
  check: lcc: OK steps=26300 6h_regular=True 2004-01-01 00:00..2021-12-31 18:00 grid=61x141 NaN=0 values_identical_to_chunks=True
  sha256: e051deedb7ea4c4200d47a29275546ffadd48510699216152d2d8a7927c8451d
