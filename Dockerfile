FROM python:3.12

# Set working directory
WORKDIR /code

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Copy Poetry configuration files
COPY poetry.lock pyproject.toml ./

RUN poetry config virtualenvs.create false

# Install dependencies (runtime only)
RUN poetry install --no-dev

# Copy the entire project
COPY . .

# Expose the port that the application will run on
EXPOSE 8000

# Command to run the application
CMD [""]