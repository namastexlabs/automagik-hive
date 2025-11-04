"""
Real Agent Execution Tests - NO MOCKING.

These tests actually call OpenAI and Anthropic APIs to verify agents work.
They measure response quality, latency, and reliability.

Requirements:
- OPENAI_API_KEY set in environment
- ANTHROPIC_API_KEY set in environment
- API credits available

Run with: uv run pytest tests/integration/agents/test_real_agent_execution.py -v -s
"""

import asyncio
import time

import pytest


@pytest.mark.integration
class TestRealAgentExecution:
    """Test real agent execution with actual API calls."""

    @pytest.mark.asyncio
    async def test_openai_agent_responds(
        self,
        verify_api_keys,
        create_test_agent,
        test_agent_configs,
        test_queries,
        quality_validator,
        test_results_logger,
    ):
        """Test OpenAI agent actually responds to queries."""
        # GIVEN: Real OpenAI agent
        config = test_agent_configs["openai_simple"]
        agent = create_test_agent(config)
        query_config = test_queries["simple_greeting"]

        print("\n=== Testing OpenAI Agent ===")
        print(f"Model: {config['model']['id']}")
        print(f"Query: {query_config['query']}")

        # WHEN: Running query with real API
        start = time.time()
        try:
            response = await agent.arun(query_config["query"])
            duration = time.time() - start

            # THEN: Agent responds
            assert response is not None, "No response from agent"
            assert hasattr(response, "content"), "Response missing content"
            content = response.content

            print(f"Response: {content[:200]}...")
            print(f"Duration: {duration:.2f}s")

            # Validate quality
            validation = quality_validator.validate_response(content, query_config)
            quality_score = quality_validator.calculate_quality_score(validation)

            print(f"Quality Score: {quality_score:.2%}")
            print(f"Validation: {validation}")

            # Quality assertions
            assert validation["has_content"], "Response is empty"
            assert validation["min_length"], f"Response too short: {len(content)} chars"
            assert validation["not_error"], "Response contains error message"
            assert quality_score >= 0.75, f"Quality too low: {quality_score:.2%}"

            # Performance assertion
            assert duration < query_config["timeout"], f"Response too slow: {duration}s"

            test_results_logger.log_test(
                "openai_simple_query", True, duration, {"quality_score": quality_score, "response_length": len(content)}
            )

            print("✅ OpenAI agent test PASSED")

        except Exception as e:
            test_results_logger.log_test("openai_simple_query", False, time.time() - start, {"error": str(e)})
            raise

    @pytest.mark.asyncio
    async def test_anthropic_agent_responds(
        self,
        verify_api_keys,
        create_test_agent,
        test_agent_configs,
        test_queries,
        quality_validator,
        test_results_logger,
    ):
        """Test Anthropic agent actually responds to queries."""
        # GIVEN: Real Anthropic agent
        config = test_agent_configs["anthropic_simple"]
        agent = create_test_agent(config)
        query_config = test_queries["factual_question"]

        print("\n=== Testing Anthropic Agent ===")
        print(f"Model: {config['model']['id']}")
        print(f"Query: {query_config['query']}")

        # WHEN: Running query with real API
        start = time.time()
        try:
            response = await agent.arun(query_config["query"])
            duration = time.time() - start

            # THEN: Agent responds
            assert response is not None
            content = response.content

            print(f"Response: {content[:200]}...")
            print(f"Duration: {duration:.2f}s")

            # Validate quality
            validation = quality_validator.validate_response(content, query_config)
            quality_score = quality_validator.calculate_quality_score(validation)

            print(f"Quality Score: {quality_score:.2%}")
            print(f"Validation: {validation}")

            # Quality assertions
            assert validation["has_content"]
            assert validation["min_length"]
            assert validation["contains_keywords"], f"Missing expected keywords in: {content}"
            assert quality_score >= 0.75

            # Performance assertion
            assert duration < query_config["timeout"]

            test_results_logger.log_test(
                "anthropic_factual_query",
                True,
                duration,
                {"quality_score": quality_score, "response_length": len(content)},
            )

            print("✅ Anthropic agent test PASSED")

        except Exception as e:
            test_results_logger.log_test("anthropic_factual_query", False, time.time() - start, {"error": str(e)})
            raise

    @pytest.mark.asyncio
    async def test_math_specialist_agent(
        self,
        verify_api_keys,
        create_test_agent,
        test_agent_configs,
        test_queries,
        quality_validator,
        test_results_logger,
    ):
        """Test specialized agent with specific task."""
        # GIVEN: Math specialist agent
        config = test_agent_configs["math_specialist"]
        agent = create_test_agent(config)
        query_config = test_queries["math_question"]

        print("\n=== Testing Math Specialist ===")
        print(f"Query: {query_config['query']}")

        # WHEN: Running math query
        start = time.time()
        try:
            response = await agent.arun(query_config["query"])
            duration = time.time() - start

            content = response.content
            print(f"Response: {content}")
            print(f"Duration: {duration:.2f}s")

            # Validate quality
            validation = quality_validator.validate_response(content, query_config)
            quality_score = quality_validator.calculate_quality_score(validation)

            # THEN: Correct answer present
            assert "391" in content, f"Incorrect answer in: {content}"
            assert validation["has_content"]
            assert quality_score >= 0.75

            test_results_logger.log_test(
                "math_specialist_query", True, duration, {"quality_score": quality_score, "correct_answer": True}
            )

            print("✅ Math specialist test PASSED")

        except Exception as e:
            test_results_logger.log_test("math_specialist_query", False, time.time() - start, {"error": str(e)})
            raise

    @pytest.mark.asyncio
    async def test_creative_writer_agent(
        self,
        verify_api_keys,
        create_test_agent,
        test_agent_configs,
        test_queries,
        quality_validator,
        test_results_logger,
    ):
        """Test creative agent with high temperature."""
        # GIVEN: Creative writer agent
        config = test_agent_configs["creative_writer"]
        agent = create_test_agent(config)
        query_config = test_queries["creative_prompt"]

        print("\n=== Testing Creative Writer ===")
        print(f"Temperature: {config['model']['temperature']}")
        print(f"Query: {query_config['query']}")

        # WHEN: Running creative query
        start = time.time()
        try:
            response = await agent.arun(query_config["query"])
            duration = time.time() - start

            content = response.content
            print(f"Response: {content}")
            print(f"Duration: {duration:.2f}s")

            # Validate quality
            validation = quality_validator.validate_response(content, query_config)
            quality_score = quality_validator.calculate_quality_score(validation)

            # THEN: Creative output present
            assert validation["has_content"]
            assert validation["min_length"]
            assert validation["contains_keywords"]
            assert quality_score >= 0.75

            test_results_logger.log_test(
                "creative_writer_query",
                True,
                duration,
                {"quality_score": quality_score, "response_length": len(content)},
            )

            print("✅ Creative writer test PASSED")

        except Exception as e:
            test_results_logger.log_test("creative_writer_query", False, time.time() - start, {"error": str(e)})
            raise

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(
        self, verify_api_keys, create_test_agent, test_agent_configs, quality_validator, test_results_logger
    ):
        """Test agent maintains context across multiple turns."""
        # GIVEN: Agent with conversation
        config = test_agent_configs["openai_simple"]
        agent = create_test_agent(config)

        print("\n=== Testing Multi-Turn Conversation ===")

        start = time.time()
        try:
            # Turn 1
            print("Turn 1: Setting context...")
            response1 = await agent.arun("My favorite color is blue.")
            content1 = response1.content
            print(f"Response 1: {content1[:100]}...")

            assert content1, "No response to turn 1"

            # Turn 2 - Reference previous context
            print("Turn 2: Testing context recall...")
            response2 = await agent.arun("What is my favorite color?")
            content2 = response2.content
            print(f"Response 2: {content2}")

            duration = time.time() - start

            # THEN: Agent remembers context
            assert "blue" in content2.lower(), f"Agent forgot context: {content2}"
            print(f"Duration: {duration:.2f}s")

            test_results_logger.log_test("multi_turn_conversation", True, duration, {"context_retained": True})

            print("✅ Multi-turn conversation test PASSED")

        except Exception as e:
            test_results_logger.log_test("multi_turn_conversation", False, time.time() - start, {"error": str(e)})
            raise


@pytest.mark.integration
class TestAgentReliability:
    """Test agent reliability and error handling."""

    @pytest.mark.asyncio
    async def test_handles_empty_query(self, verify_api_keys, create_test_agent, test_agent_configs):
        """Test agent handles empty query gracefully."""
        # GIVEN: Agent
        config = test_agent_configs["openai_simple"]
        agent = create_test_agent(config)

        print("\n=== Testing Empty Query Handling ===")

        # WHEN: Empty query
        try:
            response = await agent.arun("")
            # THEN: Should handle gracefully
            assert response is not None
            print("✅ Empty query handled")
        except Exception as e:
            # Some providers may reject empty queries
            print(f"Empty query rejected (expected): {e}")
            assert "empty" in str(e).lower() or "required" in str(e).lower()

    @pytest.mark.asyncio
    async def test_handles_very_long_query(
        self, verify_api_keys, create_test_agent, test_agent_configs, test_results_logger
    ):
        """Test agent handles long queries."""
        # GIVEN: Agent
        config = test_agent_configs["openai_simple"]
        agent = create_test_agent(config)

        print("\n=== Testing Long Query ===")

        # WHEN: Very long query (but within limits)
        long_query = "Tell me about " + ("the history of technology " * 50)
        print(f"Query length: {len(long_query)} chars")

        start = time.time()
        try:
            response = await agent.arun(long_query)
            duration = time.time() - start

            # THEN: Handles successfully
            assert response.content
            print(f"Response length: {len(response.content)} chars")
            print(f"Duration: {duration:.2f}s")

            test_results_logger.log_test(
                "long_query_handling",
                True,
                duration,
                {"query_length": len(long_query), "response_length": len(response.content)},
            )

            print("✅ Long query handled")

        except Exception as e:
            test_results_logger.log_test("long_query_handling", False, time.time() - start, {"error": str(e)})
            raise

    @pytest.mark.asyncio
    async def test_concurrent_requests(
        self, verify_api_keys, create_test_agent, test_agent_configs, test_results_logger
    ):
        """Test agent handles concurrent requests."""
        # GIVEN: Multiple agents
        config = test_agent_configs["openai_simple"]
        agents = [create_test_agent(config) for _ in range(3)]

        print("\n=== Testing Concurrent Requests ===")

        # WHEN: Running concurrent queries
        queries = ["What is 2+2?", "What is the capital of Japan?", "Name a primary color."]

        start = time.time()
        try:
            # Run all concurrently
            responses = await asyncio.gather(
                *[agent.arun(query) for agent, query in zip(agents, queries, strict=False)]
            )
            duration = time.time() - start

            # THEN: All succeed
            assert len(responses) == 3
            for i, response in enumerate(responses):
                assert response.content, f"Response {i} empty"
                print(f"Response {i}: {response.content[:100]}...")

            print(f"Total duration: {duration:.2f}s")
            print(f"Average per request: {duration / 3:.2f}s")

            test_results_logger.log_test(
                "concurrent_requests", True, duration, {"num_requests": 3, "avg_duration": duration / 3}
            )

            print("✅ Concurrent requests handled")

        except Exception as e:
            test_results_logger.log_test("concurrent_requests", False, time.time() - start, {"error": str(e)})
            raise


@pytest.mark.integration
class TestAgentPerformance:
    """Test agent performance characteristics."""

    @pytest.mark.asyncio
    async def test_response_time_consistency(
        self, verify_api_keys, create_test_agent, test_agent_configs, measure_response_time, test_results_logger
    ):
        """Test that response times are reasonably consistent."""
        # GIVEN: Agent
        config = test_agent_configs["openai_simple"]
        agent = create_test_agent(config)
        query = "What is 1+1?"

        print("\n=== Testing Response Time Consistency ===")

        # WHEN: Multiple requests
        times = []
        for i in range(5):
            with measure_response_time() as timer:
                response = await agent.arun(query)
                assert response.content
            times.append(timer.duration)
            print(f"Request {i + 1}: {timer.duration:.2f}s")
            await asyncio.sleep(0.5)  # Rate limiting

        # THEN: Times are consistent
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        print(f"Average: {avg_time:.2f}s")
        print(f"Range: {min_time:.2f}s - {max_time:.2f}s")

        # Variance shouldn't be too high
        variance = max_time - min_time
        print(f"Variance: {variance:.2f}s")

        test_results_logger.log_test(
            "response_time_consistency",
            True,
            avg_time,
            {"avg": avg_time, "min": min_time, "max": max_time, "variance": variance},
        )

        assert variance < 10.0, f"Response time too inconsistent: {variance}s variance"

        print("✅ Response times consistent")
