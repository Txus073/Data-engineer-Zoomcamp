#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from sqlalchemy import create_engine

engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')

df_zone = pd.read_csv('taxi+_zone_lookup.csv')

df_zone.to_sql(name='zone', con=engine, if_exists='replace')


