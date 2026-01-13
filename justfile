
set positional-arguments

alias p := pre-commit
alias pa := pre-commit-all
alias t := test
alias c := coverage

# pre-commit the current changes
pre-commit *ARGS:
    git add .
    pre-commit {{ARGS}}

# pre-commit all repo files
pre-commit-all:
    git add .
    pre-commit run --all

# test the specified path (uses latest Python)
test *ARGS:
    tox -e path -- {{ARGS}}

# run coverage tests
coverage:
    git add .
    pre-commit run tox
