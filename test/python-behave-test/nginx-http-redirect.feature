Feature: Rediect HTTP to HTTPs
  Scenario: Consume http://localhost:8888
    When a Nginx container is running
    Then I make GET request to http://localhost:8888 then I should get redirected and receive 200
