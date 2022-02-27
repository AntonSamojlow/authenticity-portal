# authenticity-portal
This is a prototype of a web site/server (currently hosted under https://authenticity-portal.herokuapp.com/) which 
- serves selected 'prediction models'\* to a general audience
- presents the models within a specific topic (use case), providing additional information and context

It is named *authenticity-portal* to indicate one possible field of application: 
        A platform where one can upload some (measurement) data of a food to verify/predict 
        certain properties, like authenticity of the geographical organic. The prediction models 
        are curated and validated by trusted institutions. 
        
(\*note that in my terminology, prediction models include classification)

# Design description

## Targeted use case 
The portal is designed to accomodate two different work flows (and user types):

- The **general user** uses validated models to obtain information about their dataset. For example:
    - a quantitative prediction, like the nutrient content of a sample
    - a classification, like the authenticity of a sample (likelihood of class member ship)
   This user typically has limited access, the main interaction with the portal being:
    - access details/information about the selected topics and the available models
    - request a prediction by feeding a data file to one of the hosted models  

- The **data manager** or **scientist** curates the validated models. This involves 
    - upload of measurment data
    - generation of models
    - training of models on selæected measurements
    - validation/staging a model for use by general users
    This user typically has advanced access to the site. which might include access to the backing data.

## Implementation highlights
This is my first web site, where I focussed mainly on the web server part and much less on the frontend.

One highlight is the custom port of the Simca model from R ([mdatools](https://mdatools.com/docs/simca.html)) to python, thereby providing an interesting use case that goes beyond usual calssification models.   

## Technical tools
- Backend / web server framework: [django (python)](https://www.djangoproject.com/) 
- Frontend framework: [Bootstrap 5.0](https://getbootstrap.com/docs/)
- Configured for deplyment on the [heroku platform](https://www.heroku.com)


# Deployment instructions
The subfolder `portalsite` is setup for deployment to heroku (with a Postgres db), for example by the git command

```
git subtree push --prefix portalsite heroku main
```

and contains therefore i.p. the files
- requirements.txt
- runtime.txt
- Procfile

Note that the target environment is expected to provide the variables 'DATABASE_URL', 'DJANGO_DEBUG' and 'DJANGO_SECRET_KEY'.
And if required, a superuser should be created after intial deployment, see heroku and django docs for details.

The database can be seeded via heroku CLI with the command
```
heroku run python manage.py loaddata portal/fixtures/initial_seed_data.json
```
This will create iris-example data with two models (trained on Setosa) as well as two users
- 'generic_test_user', password 'GENER1C!' with only basic rights
- 'scientist_test_user', password 'SC1ENCE!' with rights to all portal objects and selected administration privileges

