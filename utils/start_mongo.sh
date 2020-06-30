docker run -d -p 27017:27017 -e MONGO_INITDB_ROOT_USERNAME=pyauthadmin \
                             -e MONGO_INITDB_ROOT_PASSWORD=password \
                             -e MONGO_INITDB_DATABASE=pyauth \
                             mongo
