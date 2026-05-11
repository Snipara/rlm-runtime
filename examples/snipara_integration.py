#!/usr/bin/env python3
"""
Snipara Integration Example

This example demonstrates using Snipara Sandbox with Snipara
for intelligent context retrieval and memory.
"""

import asyncio

from snipara_sandbox import SniparaSandbox


async def main():
    """Run Snipara integration examples."""
    # Create Snipara Sandbox with Snipara configuration
    # Get your API key from https://snipara.com/dashboard
    sandbox = SniparaSandbox(
        model="gpt-4o-mini",
        snipara_api_key="snp-your-api-key-here",
        snipara_project_slug="your-project-slug",
        # Enable memory tools for persistent context
        # memory_enabled=True,
    )

    # Example 1: Query documentation
    print("=== Query Documentation ===")
    result = await sandbox.completion("""
        How does the authentication system work in this codebase?
        Use the documentation to find:
        - Auth flow
        - Code examples
        - Security considerations
    """)
    print(f"Response: {result.response[:500]}...")
    print()

    # Example 2: Search for patterns
    print("=== Search for Patterns ===")
    result = await sandbox.completion("""
        Find all error handling patterns in the codebase.
        Show examples of:
        - Try/except blocks
        - Error logging
        - User-facing error messages
    """)
    print(f"Response: {result.response[:500]}...")
    print()

    # Example 3: Code generation with context
    print("=== Code Generation with Context ===")
    result = await sandbox.completion("""
        Create a new API endpoint for user registration.
        Follow the existing patterns from the documentation:
        - Use the same error handling
        - Follow the authentication flow
        - Include proper validation
    """)
    print(f"Response: {result.response[:500]}...")
    print()

    # Example 4: Team guidelines
    print("=== Team Guidelines ===")
    result = await sandbox.completion("""
        What are the team's coding standards for this project?
        Include:
        - Code style guidelines
        - Testing requirements
        - Documentation standards
    """)
    print(f"Response: {result.response[:500]}...")
    print()


# Example with Memory (requires memory_enabled=True)
async def memory_example():
    """Example using memory features."""
    sandbox = SniparaSandbox(
        model="gpt-4o-mini",
        snipara_api_key="snp-your-api-key-here",
        snipara_project_slug="your-project-slug",
        memory_enabled=True,  # Enable memory tools
    )

    # Store a decision
    print("=== Store Memory ===")
    result = await sandbox.completion(
        "We decided to use PostgreSQL as our primary database "
        "because of its reliability and feature set."
    )
    print("Memory stored successfully")
    print()

    # Later, recall the decision
    print("=== Recall Memory ===")
    result = await sandbox.completion("What database are we using for this project?")
    print(f"Response: {result.response}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
    # Uncomment to run memory example:
    # asyncio.run(memory_example())
