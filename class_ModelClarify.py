import numpy as np
import pandas as pd 
from treeinterpreter import treeinterpreter as ti

list_of_acceptable_tree_models = ['RandomForestClassifier', 'RandomForestRegressor',
    'DecisionTreeClassifier', 'ExtraTreesClassifier', 'ExtraTreesRegressor']

class ModelClarify():

    '''
    Class for computing various ML model interpretations...blah blah blah

    '''

    def __init__(self, model, examples_in, targets_in, classification=True):

        self._model    = model
        self._examples = examples_in
        self._targets  = targets_in
        self._feature_names  = examples_in.columns.to_list()

        self._classification = classification

    def tree_interpreter_performance_based(self, performance_dict=None):

        '''
        Method for intrepreting tree based ML models using treeInterpreter. 
        Uses indices from dictionary returned by get_indices_based_on_performance()

        ADD REFERENCE HERE SOMEWHERE

        '''

        # check to make sure model is of type Tree
        if (type(self._model).__name__ not in list_of_acceptable_tree_models):
            raise Exception(f'{model_name} model is not accepted for this method.')                
        
        if (performance_dict is None): self.get_indices_based_on_performance()

        # will be returned; a list of pandas dataframes, one for each performance dict key
        list_of_dfs = []

        for key,values in zip(performance_dict.keys(), performance_dict.values()):

            # number of examples
            n_examples = values.shape[0]

            # get examples for key
            tmp_examples = self._examples.loc[values,:]

            print( f'Interpreting {n_examples} examples from {key}')
            prediction, bias, contributions = ti.predict( self._model, tmp_examples)

            forecast_probabilities = self._model.predict_proba(tmp_examples)[:,1]*100.
            positive_class_contributions = contributions[:,:,1]

            tmp_data = []
    
            #loop over each case appending and append each feature and value to a dictionary
            for i in range(n_examples):

                key_list = []
                var_list = []

                for c, feature in zip(positive_class_contributions[i,:], self._feature_names):
    
                    key_list.append(feature)
                    var_list.append(round(100.0*c,2))
     
                tmp_data.append(dict(zip(key_list,var_list))) 
    
            #return a pandas DataFrame to do analysis on
            contributions_dataframe = pd.DataFrame(data=tmp_data)

            list_of_dfs.append(contributions_dataframe)

        return list_of_dfs 

    def tree_interpreter_simple(self):

        '''
        Method for intrepreting tree based ML models using treeInterpreter.
        Uses all data passed in to constructor
 
        ADD REFERENCE HERE SOMEWHERE

        '''

        #check to make sure model is of type Tree
        if (type(self._model).__name__ not in list_of_acceptable_tree_models):
            raise Exception(f'{model_name} model is not accepted for this method.')                

        #number of examples
        n_examples = self._examples.shape[0]

        print( f'Interpreting {n_examples} examples...')
        prediction, bias, contributions = ti.predict( self._model, self._examples)

        forecast_probabilities = self._model.predict_proba(self._examples)[:,1]*100.
        positive_class_contributions = contributions[:,:,1]

        tmp_data = []
    
        #loop over each case appending and append each feature and value to a dictionary
        for i in range(n_examples):

            key_list = []
            var_list = []

            for c, feature in zip(positive_class_contributions[i,:], self._feature_names):
    
                key_list.append(feature)
                var_list.append(round(100.0*c,2))
     
            tmp_data.append(dict(zip(key_list,var_list))) 
    
        #return a pandas DataFrame to do analysis on
        contributions_dataframe = pd.DataFrame(data=tmp_data)

        return contributions_dataframe 

    def compute_1d_partial_dependence(self, feature=None, **kwargs):

        '''
        Calculate the partial dependence.
        # Friedman, J., 2001: Greedy function approximation: a gradient boosting machine.Annals of Statistics,29 (5), 1189–1232.
        ##########################################################################
        Partial dependence plots fix a value for one or more predictors
        # for examples, passing these new data through a trained model, 
        # and then averaging the resulting predictions. After repeating this process
        # for a range of values of X*, regions of non-zero slope indicates that
        # where the ML model is sensitive to X* (McGovern et al. 2019). Only disadvantage is
        # that PDP do not account for non-linear interactions between X and the other predictors.
        #########################################################################

        Args: 
            feature : name of feature to compute PD for (string) 
        '''
    
        # check to make sure a feature is present...
        if (feature is None): raise Exception('Specify a feature')

        #check to make sure feature is valid
        if (feature not in self._feature_names): 
            raise Exception(f'Feature {feature} is not a valid feature')

        print("Computing 1-D partial dependence...")

        # get data in numpy format
        column_of_data = self._examples[feature].to_numpy()

        # define bins based on 10th and 90th percentiles
        variable_range = np.linspace(np.percentile(column_of_data, 10), 
                                     np.percentile(column_of_data, 90), num = 20)

        # define output array to store partial dependence values
        pdp_values = np.full(variable_range.shape[0], np.nan)

        # for each value, set all indices to the value, make prediction, store mean prediction
        for i, value in enumerate(variable_range):
        
            copy_df = self._examples.copy()
            copy_df.loc[:,feature] = value

            if (self._classification is True): 
                predictions = self._model.predict_proba( copy_df)[:,1]
            else:
                predictions = self._model.predict( copy_df)
            
            pdp_values[i] = np.mean(predictions)

        return pdp_values, variable_range

    def compute_2d_partial_dependence(self, features, **kwargs):

        '''
        Calculate the partial dependence.
        # Friedman, J., 2001: Greedy function approximation: a gradient boosting machine.Annals of Statistics,29 (5), 1189–1232.
        ##########################################################################
        Partial dependence plots fix a value for one or more predictors
        # for examples, passing these new data through a trained model, 
        # and then averaging the resulting predictions. After repeating this process
        # for a range of values of X*, regions of non-zero slope indicates that
        # where the ML model is sensitive to X* (McGovern et al. 2019). Only disadvantage is
        # that PDP do not account for non-linear interactions between X and the other predictors.
        #########################################################################

        Args: 
            feature : tuple of type string of predictor names

        '''
    
        # make sure there are two features...
        if (len(features) > 2): raise Exception(f'tuple of size {len(features)} is greater than 2')
        if (len(features) < 2): raise Exception(f'tuple of size {len(features)} is less than 2')

        # make sure both features are valid...
        if (feature[0] is None or feature[1] is None): 
            raise Exception('One or more features is of type None.')

        #check to make sure feature is valid
        if (feature[0] not in self._feature_names or feature[1] not in self._feature_names): 
            raise Exception(f'Feature {feature} is not a valid feature')


        # get data for both features
        values_for_var1 = self._examples[features[0]].to_numpy()
        values_for_var2 = self._examples[features[1]].to_numpy()

        # get ranges of data for both features
        var1_range = np.linspace(np.percentile(values_for_var1, 10), 
                                 np.percentile(values_for_var1, 90), num = 20 )
        var2_range = np.linspace(np.percentile(values_for_var2, 10), 
                                 np.percentile(values_for_var2, 90), num = 20 )

        # define 2-D grid
        pdp_values = np.full((var1_range.shape[0], var2_range.shape[0]), np.nan)

        # similar concept as 1-D, but for 2-D
        for i, value1 in enumerate(var1_range):
            for k, value2 in enumerate(var2_range):
                copy_df = self._examples.copy()
                copy_df.loc[features[0]] = value1
                copy_df.loc[features[1]] = value2

                if (self._classification is True): 
                    predictions = self._model.predict_proba( copy_df)[:,1]
                else:
                    predictions = self._model.predict( copy_df)

                pdp_values[i,k] = np.mean(predictions)

        return pdp_values, var1_range, var2_range

    def calculate_first_order_ALE(self, feature=None, quantiles=None):

        """Computes first-order ALE function on single continuous feature data.

        Parameters
        ----------
        feature : string
            Feature's name.
        quantiles : array
            Quantiles of feature.
        """
        
        # make sure feature is set
        if (feature is None): raise Exception('Specify a feature.')

        # convert quantiles to array if list
        if isinstance(quantiles, list): quantiles = np.array(quantiles)

        if (quantiles is None):
            quantiles = np.linspace(np.percentile(all_values,10), 
                                    np.percentile(all_values,90), num = 20)

        # define ALE function
        ALE = np.zeros(len(quantiles) - 1)

        # loop over all ranges
        for i in range(1, len(quantiles)):
    
            # get subset of data
            subset = self._examples[(quantiles[i - 1] <= self._examples[feature]) & 
                                    (self._examples[feature] < quantiles[i])]

            # Without any observation, local effect on splitted area is null
            if len(subset) != 0:
                z_low = subset.copy()
                z_up  = subset.copy()

                # The main ALE idea that compute prediction difference between same data except feature's one
                z_low[feature] = quantiles[i - 1]
                z_up[feature]  = quantiles[i]
    
                if (self._classification is True):
                    ALE[i - 1] += (self._model.predict_proba(z_up) - self._model.predict_proba(z_low)).sum() / subset.shape[0]
                else:
                    ALE[i - 1] += (self._model.predict(z_up) - self._model.predict(z_low)).sum() / subset.shape[0]
          
        # The accumulated effect      
        ALE = ALE.cumsum()  

        # Now we have to center ALE function in order to obtain null expectation for ALE function
        ALE -= ALE.mean()

        return ALE


    def get_indices_based_on_performance(self, num_indices=10):

        '''
        Determines the best 'hits' (forecast probabilties closest to 1)
        or false alarms (forecast probabilities furthest from 0 )
        or misses (forecast probabilties furthest from 1 )

        The returned dictionary below can be passed into interpert_tree_based_model()

        Args:
        ------------------
            num_indices : Integer representing the number of indices (examples) to return.
                          Default is 10
        '''
        
        if isinstance(self._examples, pd.DataFrame): examples_cp = self._examples.to_numpy()

        #get indices for each binary class
        positive_idx = np.where(self._targets > 0)
        negative_idx = np.where(self._targets < 1)

        #get targets for each binary class
        positive_class = self._targets[positive_idx[0]]
        negative_class = self._targets[negative_idx[0]]    
    
        #compute forecast probabilities for each binary class
        forecast_probabilities_on_pos_class = self._model.predict_proba(examples_cp[positive_idx[0], :])[:,1]
        forecast_probabilities_on_neg_class = self._model.predict_proba(examples_cp[negative_idx[0], :])[:,1]
    
        #compute the absolute difference
        diff_from_pos = abs(positive_class - forecast_probabilities_on_pos_class)
        diff_from_neg = abs(negative_class - forecast_probabilities_on_neg_class)
    
        #sort based on difference and store in array
        sorted_diff_for_hits = np.array( sorted( zip(diff_from_pos, positive_idx[0]), key = lambda x:x[0]))
        sorted_diff_for_misses = np.array( sorted( zip(diff_from_pos, positive_idx[0]), key = lambda x:x[0], reverse=True ))
        sorted_diff_for_false_alarms = np.array( sorted( zip(diff_from_neg, negative_idx[0]), key = lambda x:x[0], reverse=True )) 

        #store all resulting indicies in one dictionary
        adict =  { 
                    'hits': [ sorted_diff_for_hits[i][1] for i in range(num_indices+1) ],
                    'false_alarms': [ sorted_diff_for_false_alarms[i][1] for i in range(num_indices+1) ],
                    'misses': [ sorted_diff_for_misses[i][1] for i in range(num_indices+1) ]
                    } 

        for key in list(adict.keys()):
            adict[key] = np.array(adict[key]).astype(int)

        return adict  
