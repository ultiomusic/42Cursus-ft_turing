NAME = ft_turing
SRC  = main.py

all: $(NAME)

$(NAME): $(SRC)
	@printf '%s\n' '#!/usr/bin/env python3' > $(NAME)
	@cat $(SRC) >> $(NAME)
	@chmod +x $(NAME)

clean:

fclean: clean
	@rm -f $(NAME)

re: fclean all

.PHONY: all clean fclean re
