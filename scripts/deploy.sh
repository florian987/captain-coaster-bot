#!/bin/bash

# Build and deploy on master branch
if [[ $CI_COMMIT_REF_SLUG == 'master' ]]; then
    #echo "Connecting to docker hub"
    #echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

    ci_changed_lines=$(git diff HEAD~1 HEAD docker/ci.Dockerfile | wc -l)
    base_changed_lines=$(git diff HEAD~1 HEAD docker/Dockerfile.base | wc -l)

    if [ $ci_changed_lines != '0' ]; then
      echo "ci.Dockerfile was changed"

      echo "Building bot ci"
      docker build -t $CI_REGISTRY_IMAGE:ci -f docker/ci.Dockerfile .

      echo "Pushing image to Docker Hub"
      docker push $CI_REGISTRY_IMAGE:ci
    else
      echo "ci.Dockerfile was not changed, not building"
    fi

    if [ $base_changed_lines != '0' ]; then
      echo "Dockerfile.base was changed"

      echo "Building bot base"
      docker build -t $CI_REGISTRY_IMAGE:base -f docker/Dockerfile.base .

      echo "Pushing image to Docker Hub"
      docker push $CI_REGISTRY_IMAGE:base
    else
      echo "Dockerfile.base was not changed, not building"
    fi

    echo "Building image"
    docker build -t $CI_REGISTRY_IMAGE:latest -f docker/Dockerfile .

    echo "Pushing image"
    docker push $CI_REGISTRY_IMAGE:latest

else
    echo "Skipping deploy"
fi
