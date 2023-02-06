"""
This is a boilerplate pipeline 'data_processing'
generated using Kedro 0.18.4
"""
import pandas as pd
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import udf,col
from pyspark.sql.types import BooleanType, FloatType


@udf(returnType=BooleanType())
def _is_true(x: str) -> bool:
    return x == "t"

@udf(returnType=FloatType())
def _parse_percentage(x: str) -> float:
    if isinstance(x,str):
        x = x.replace("%", "")
        x = float(x) / 100
    return x

@udf(returnType=FloatType())
def _parse_money(x: str) -> float:
    if isinstance(x,str):
        x = x.replace("$", "").replace(",", "")
        x = float(x)
    return x


def preprocess_companies(companies: DataFrame) -> DataFrame:
    """Preprocesses the data for companies.

    Args:
        companies: Raw data.
    Returns:
        Preprocessed data, with `company_rating` converted to a float and
        `iata_approved` converted to boolean.
    """
    #companies["iata_approved"] = _is_true(companies["iata_approved"])
    #companies["company_rating"] = _parse_percentage(companies["company_rating"])
    companies = companies.withColumn("iata_approved", _is_true(companies.iata_approved))
    companies = companies.withColumn("company_rating", _parse_percentage(companies.company_rating))
    return companies


def preprocess_shuttles(shuttles: pd.DataFrame) -> DataFrame:
    """Preprocesses the data for shuttles.

    Args:
        shuttles: Raw data.
    Returns:
        Preprocessed data, with `price` converted to a float and `d_check_complete`,
        `moon_clearance_complete` converted to boolean.
    """
    spark = SparkSession.builder.getOrCreate()
    sdf = spark.createDataFrame(shuttles)
    sdf = sdf.withColumn("d_check_complete", _is_true(sdf.d_check_complete))
    sdf = sdf.withColumn("moon_clearance_complete", _is_true(sdf.moon_clearance_complete))
    sdf = sdf.withColumn("price", _parse_money(sdf.price))
    #shuttles["d_check_complete"] = _is_true(shuttles["d_check_complete"])
    #shuttles["moon_clearance_complete"] = _is_true(shuttles["moon_clearance_complete"])
    #shuttles["price"] = _parse_money(shuttles["price"])
    return sdf

def create_model_input_table(
    shuttles: DataFrame, companies: DataFrame, reviews: DataFrame
) -> pd.DataFrame:
    """Combines all data to create a model input table.

    Args:
        shuttles: Preprocessed data for shuttles.
        companies: Preprocessed data for companies.
        reviews: Raw data for reviews.
    Returns:
        model input table.

    """
    rated_shuttles = shuttles.join(reviews, shuttles.id == reviews.shuttle_id, "inner")
    model_input_table = rated_shuttles.join(companies,
        rated_shuttles.company_id == companies.id, "inner"
    )
    model_input_table = model_input_table.drop("id")
    model_input_table = model_input_table.na.drop()
    return model_input_table