SOURCE          = ./build/html
DEPLOY          = ./_deploy
DEPLOY_SUBDIR   = ./
BRANCH          = gh-pages
REPO            = git@github.com:dtaylor84/pysnapsync

#######################################################################

SHELL:=/bin/bash -x

SOURCEDIR=$(shell readlink -e $(SOURCE))
DEPLOYDIR=$(shell readlink -f $(DEPLOY))
HTMLDIR=$(shell readlink -f $(DEPLOYDIR)/$(DEPLOY_SUBDIR))

init:
	@echo "This will blow away any existing $(BRANCH) branch!" 
	@read -p "Are you sure? Y to confirm: " -n 1 -r -s && [[ "$$REPLY" == "Y" ]]
	@rm -Rf $(DEPLOYDIR)
	@mkdir -p $(DEPLOYDIR)
	@cd $(DEPLOYDIR) && \
		git init && \
		git remote add origin $(REPO) && \
		git checkout --orphan $(BRANCH) && \
		touch .nojekyll && \
		git add .nojekyll && \
		git commit -m "Initial $(BRANCH) branch" && \
		git push -f -u origin $(BRANCH) --quiet

setup:
	@rm -Rf $(DEPLOYDIR)
	@mkdir -p $(DEPLOYDIR)
	@cd $(DEPLOYDIR) && \
		git clone -b $(BRANCH) --single-branch $(REPO) .

deploy:
	@shopt -s extglob && \
		cd $(DEPLOYDIR) && \
		git fetch -f origin $(BRANCH) && \
		git reset --hard FETCH_HEAD && \
		rm -Rf ./* && \
		mkdir -p $(HTMLDIR) && \
		[[ -d "$(SOURCEDIR)" ]] && \
		cp -R $(SOURCEDIR)/. $(HTMLDIR) && \
		if [[ $$(git status --porcelain) ]]; then \
			git add -A && \
			git commit -m "Automated docs deployment" && \
			git push origin $(BRANCH) --quiet; \
		fi

html:
	        http_proxy='127.0.0.1:9' sphinx-build -N -bhtml  source build/html

man:
	        http_proxy='127.0.0.1:9' sphinx-build -N -bman   source build/man
