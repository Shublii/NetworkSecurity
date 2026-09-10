# "We create the components folder to separate each ML pipeline step into its own module, making the project clean, reusable, and easier to maintain."


from networksecurity.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact 
from networksecurity.entity.config_entity import  DataValidationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.constants.training_pipeline import SCHEMA_FILE_PATH

from scipy.stats import ks_2samp ##this is for Data drift detection
import os,sys
import pandas as pd
from networksecurity.utils.main_utils.utils import read_yaml_file , write_yaml_file

class DataValidation:
    def __init__(self, data_ingestion_artifact: DataIngestionArtifact, data_validation_config: DataValidationConfig):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
            self.schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise NetworkSecurityException(e, sys)

    @staticmethod
    def read_data(file_path)->pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise NetworkSecurityException(e, sys)    


    def validate_numbers_of_columns(self, dataframe: pd.DataFrame)->bool:
        try:
            number_of_columns = len(self.schema_config['columns'])
            logging.info(f"Required number of columns: {number_of_columns}")
            logging.info(f"Dataframe has columns: {len(dataframe.columns)}")
            if len(dataframe.columns) == number_of_columns:
                return True
            return False
        except Exception as e:
            raise NetworkSecurityException(e, sys) 

    def detect_data_drift(self, base_df , current_df, threshold=0.05)->bool:
        try:
            status=True
            report={}
            for column in base_df.columns:
                d1 = base_df[column]
                d2 = current_df[column]
                is_same_dist = ks_2samp(d1,d2)
                if threshold <= is_same_dist.pvalue:
                    is_found=False  
                else:
                    is_found=True
                    status=False
                report.update({column:{
                    "p_value":float(is_same_dist.pvalue),
                    "drift_status":is_found
                }}) 
            drift_report_file_path = self.data_validation_config.drift_report_file_path
            os.makedirs(os.path.dirname(drift_report_file_path), exist_ok=True)
            write_yaml_file(file_path=drift_report_file_path, content=report)

        except Exception as e:
            raise NetworkSecurityException(e, sys)       

    def  initiate_data_validation(self)->DataValidationArtifact:
        try:
            training_file_path = self.data_ingestion_artifact.training_file_path
            test_file_path = self.data_ingestion_artifact.test_file_path

            ##read the data from train and test file
            training_df = DataValidation.read_data(training_file_path)
            test_df = DataValidation.read_data(test_file_path)

            ##validate the number of columns
            status = self.validate_numbers_of_columns(dataframe=training_df)
            if not status:
                error_message = f"Training dataframe does not contain all columns."

            status = self.validate_numbers_of_columns(dataframe=test_df)
            if not status:
                error_message = f"Test dataframe does not contain all columns."


            ##lets check for data drift
            status=self.detect_data_drift(base_df=training_df, current_df=test_df)
            dir_path = os.path.dirname(self.data_validation_config.valid_train_file_path)
            os.makedirs(dir_path, exist_ok=True)

            training_df.to_csv(
                self.data_validation_config.valid_train_file_path, index=False, header=True
            )
            test_df.to_csv(
                            self.data_validation_config.valid_test_file_path, index=False, header=True
                        )

            
            data_validation_artifact = DataValidationArtifact(
                validation_status=status,
                valid_train_file_path=self.data_ingestion_artifact.training_file_path,
                valid_test_file_path=self.data_ingestion_artifact.test_file_path,
                invalid_train_file_path=None,
                invalid_test_file_path=None,
                drift_report_file_path=self.data_validation_config.drift_report_file_path,
            )
            return data_validation_artifact
      

        except Exception as e:
            raise NetworkSecurityException(e, sys)
    

                

        except Exception as e:
            raise NetworkSecurityException(e, sys)    






            