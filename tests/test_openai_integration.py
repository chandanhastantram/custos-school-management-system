"""
Test script to verify OpenAI integration for CUSTOS AI features.

Run this to test:
- Lesson Plan Generation
- Student AI Trainer (Quiz Generation)
- OpenAI API connectivity
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.providers.openai import OpenAIProvider
from app.core.config import settings


async def test_openai_connection():
    """Test basic OpenAI connectivity."""
    print("=" * 60)
    print("Testing OpenAI API Connection")
    print("=" * 60)
    
    if not settings.openai_api_key:
        print("❌ ERROR: OPENAI_API_KEY not configured in .env")
        return False
    
    print(f"✓ API Key configured: {settings.openai_api_key[:20]}...")
    print(f"✓ Model: {settings.openai_model}")
    print(f"✓ Max Tokens: {settings.openai_max_tokens}")
    print(f"✓ Temperature: {settings.openai_temperature}")
    
    try:
        provider = OpenAIProvider()
        print("\n✓ OpenAI provider initialized successfully")
        return True
    except Exception as e:
        print(f"\n❌ Failed to initialize OpenAI provider: {e}")
        return False


async def test_simple_generation():
    """Test simple text generation."""
    print("\n" + "=" * 60)
    print("Test 1: Simple Text Generation")
    print("=" * 60)
    
    try:
        provider = OpenAIProvider()
        
        prompt = "Explain photosynthesis in one sentence for a 10th grader."
        print(f"\nPrompt: {prompt}")
        
        response = await provider.generate_text(prompt, max_tokens=100)
        
        print(f"\n✓ Response:\n{response}")
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


async def test_lesson_plan_generation():
    """Test lesson plan generation."""
    print("\n" + "=" * 60)
    print("Test 2: Lesson Plan Generation")
    print("=" * 60)
    
    try:
        provider = OpenAIProvider()
        
        print("\nGenerating lesson plan for:")
        print("  Subject: Mathematics")
        print("  Topic: Quadratic Equations")
        print("  Grade: 10")
        print("  Duration: 45 minutes")
        
        result = await provider.generate_lesson_plan(
            subject="Mathematics",
            topic="Quadratic Equations",
            grade_level=10,
            duration_minutes=45
        )
        
        print("\n✓ Lesson Plan Generated:")
        print(f"\n  Objectives ({len(result.get('objectives', []))}):")
        for i, obj in enumerate(result.get('objectives', [])[:3], 1):
            print(f"    {i}. {obj}")
        
        print(f"\n  Introduction:")
        intro = result.get('introduction', '')
        print(f"    {intro[:150]}..." if len(intro) > 150 else f"    {intro}")
        
        print(f"\n  Activities ({len(result.get('activities', []))}):")
        for i, activity in enumerate(result.get('activities', [])[:3], 1):
            print(f"    {i}. {activity}")
        
        print(f"\n  Resources ({len(result.get('resources', []))}):")
        for i, resource in enumerate(result.get('resources', [])[:3], 1):
            print(f"    {i}. {resource}")
        
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_quiz_generation():
    """Test quiz question generation."""
    print("\n" + "=" * 60)
    print("Test 3: Quiz Question Generation")
    print("=" * 60)
    
    try:
        provider = OpenAIProvider()
        
        print("\nGenerating quiz questions:")
        print("  Subject: Physics")
        print("  Topic: Newton's Laws of Motion")
        print("  Type: MCQ")
        print("  Count: 3")
        print("  Difficulty: Medium")
        
        questions = await provider.generate_questions(
            subject="Physics",
            topic="Newton's Laws of Motion",
            question_type="mcq",
            count=3,
            difficulty="medium"
        )
        
        print(f"\n✓ Generated {len(questions)} questions:")
        
        for i, q in enumerate(questions, 1):
            print(f"\n  Question {i}:")
            print(f"    {q.get('question', 'N/A')}")
            
            if q.get('options'):
                print(f"    Options:")
                for opt in q.get('options', []):
                    print(f"      - {opt}")
            
            print(f"    Correct Answer: {q.get('correct_answer', 'N/A')}")
            
            explanation = q.get('explanation', '')
            if explanation:
                print(f"    Explanation: {explanation[:100]}..." if len(explanation) > 100 else f"    Explanation: {explanation}")
        
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_doubt_solver():
    """Test doubt solving feature."""
    print("\n" + "=" * 60)
    print("Test 4: AI Doubt Solver")
    print("=" * 60)
    
    try:
        provider = OpenAIProvider()
        
        question = "What is the difference between velocity and speed?"
        print(f"\nStudent Question: {question}")
        print(f"Subject: Physics")
        
        result = await provider.solve_doubt(
            question=question,
            subject="Physics",
            context="Kinematics chapter"
        )
        
        print(f"\n✓ AI Response:")
        print(f"\n  Answer:")
        answer = result.get('answer', '')
        print(f"    {answer[:200]}..." if len(answer) > 200 else f"    {answer}")
        
        if result.get('steps'):
            print(f"\n  Steps ({len(result['steps'])}):")
            for i, step in enumerate(result['steps'][:3], 1):
                print(f"    {i}. {step[:100]}..." if len(step) > 100 else f"    {i}. {step}")
        
        if result.get('related_concepts'):
            print(f"\n  Related Concepts:")
            for concept in result['related_concepts'][:3]:
                print(f"    - {concept}")
        
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_structured_output():
    """Test structured JSON output."""
    print("\n" + "=" * 60)
    print("Test 5: Structured Output Generation")
    print("=" * 60)
    
    try:
        provider = OpenAIProvider()
        
        prompt = "Analyze the topic 'Photosynthesis' for 9th grade students"
        schema = {
            "topic": "string",
            "difficulty": "easy|medium|hard",
            "key_concepts": ["list of concepts"],
            "prerequisites": ["list of prerequisites"],
            "learning_outcomes": ["list of outcomes"]
        }
        
        print(f"\nPrompt: {prompt}")
        print(f"Expected Schema: {schema}")
        
        result = await provider.generate_structured(prompt, schema)
        
        print(f"\n✓ Structured Response:")
        print(f"  Topic: {result.get('topic', 'N/A')}")
        print(f"  Difficulty: {result.get('difficulty', 'N/A')}")
        print(f"  Key Concepts ({len(result.get('key_concepts', []))}):")
        for concept in result.get('key_concepts', [])[:3]:
            print(f"    - {concept}")
        print(f"  Learning Outcomes ({len(result.get('learning_outcomes', []))}):")
        for outcome in result.get('learning_outcomes', [])[:3]:
            print(f"    - {outcome}")
        
        return True
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "🤖 " * 20)
    print("CUSTOS AI - OpenAI Integration Test Suite")
    print("🤖 " * 20 + "\n")
    
    results = []
    
    # Test 0: Connection
    results.append(("Connection", await test_openai_connection()))
    
    if not results[0][1]:
        print("\n❌ Cannot proceed without valid OpenAI configuration")
        return
    
    # Test 1: Simple generation
    results.append(("Simple Generation", await test_simple_generation()))
    
    # Test 2: Lesson plan
    results.append(("Lesson Plan", await test_lesson_plan_generation()))
    
    # Test 3: Quiz generation
    results.append(("Quiz Generation", await test_quiz_generation()))
    
    # Test 4: Doubt solver
    results.append(("Doubt Solver", await test_doubt_solver()))
    
    # Test 5: Structured output
    results.append(("Structured Output", await test_structured_output()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! OpenAI integration is working correctly.")
        print("\n✓ Lesson Plan AI is ready")
        print("✓ Student AI Trainer is ready")
        print("✓ Quiz generation is ready")
        print("✓ Doubt solver is ready")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
