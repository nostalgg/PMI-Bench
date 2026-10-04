from decimal import Decimal, InvalidOperation


def choose_model(request, policy):
    try:
        if (not isinstance(request, dict) or set(request) != {'data_class','input_tokens','output_tokens','task','allow_hosted'}
                or request['data_class'] not in {'public','internal','restricted'}
                or not isinstance(request['allow_hosted'], bool)
                or request['task'] not in {'sql','script','migration','classification'}
                or any(not isinstance(request[k], int) or isinstance(request[k], bool) or not 0 <= request[k] <= 10**6 for k in ['input_tokens','output_tokens'])
                or not isinstance(policy, dict) or set(policy) != {'budget_usd','models'}
                or not isinstance(policy['budget_usd'], str) or not isinstance(policy['models'], list)):
            raise ValueError('Invalid routing request')
        budget = Decimal(policy['budget_usd'])
        if not budget.is_finite() or budget < 0:
            raise ValueError('Invalid budget')
        candidates, names = [], set()
        for model in policy['models']:
            if (not isinstance(model, dict) or set(model) != {'name','deployment','tasks','context_tokens','input_per_million','output_per_million'}
                    or not isinstance(model['name'], str) or not model['name'] or model['name'] in names
                    or model['deployment'] not in {'local','hosted'} or not isinstance(model['tasks'], list)
                    or any(t not in {'sql','script','migration','classification'} for t in model['tasks'])
                    or not isinstance(model['context_tokens'], int) or isinstance(model['context_tokens'], bool)
                    or not 0 < model['context_tokens'] <= 10**6
                    or not isinstance(model['input_per_million'], str) or not isinstance(model['output_per_million'], str)):
                raise ValueError('Invalid model policy')
            names.add(model['name'])
            rates = [Decimal(model[k]) for k in ['input_per_million','output_per_million']]
            if any(not rate.is_finite() or rate < 0 or rate > 1000 for rate in rates):
                raise ValueError('Invalid price')
            cost = (request['input_tokens'] * rates[0] + request['output_tokens'] * rates[1]) / Decimal(1000000)
            if (model['deployment'] == 'hosted' and (request['data_class'] == 'restricted' or not request['allow_hosted'])):
                continue
            if request['task'] not in model['tasks'] or request['input_tokens'] + request['output_tokens'] > model['context_tokens']:
                continue
            if cost <= budget:
                candidates.append((cost,model['name']))
        if not candidates:
            raise ValueError('No eligible model')
        cost, name = min(candidates)
        return {'model': name, 'estimated_cost_usd': format(cost, 'f')}
    except (KeyError, TypeError, InvalidOperation):
        raise ValueError('Invalid routing policy') from None
