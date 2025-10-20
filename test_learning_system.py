#!/usr/bin/env python3
"""
test_learning_system.py - Test the learning system with various scenarios
"""

from meeting_learning import (
    load_learned_patterns,
    apply_learned_patterns,
    save_learned_pattern,
    add_project_alias,
    normalize_text
)

def test_title_pattern():
    """Test that title patterns are matched correctly."""
    print("\n" + "="*60)
    print("TEST 1: Title Pattern Matching")
    print("="*60)

    patterns = load_learned_patterns()

    # Test with meeting that should match title pattern
    meeting_title = "Chad : Drew : Rose 15 min stand up"
    meeting_content = "Quick sync on project status"

    result = apply_learned_patterns(meeting_title, meeting_content, patterns)

    if result:
        dest, confidence, source = result
        print(f"✓ PASS: Matched via {source}")
        print(f"  Destination: {dest['folder_name']} → {dest['list_name']}")
        print(f"  Confidence: {confidence:.0%}")
        assert source == "title_pattern", f"Expected title_pattern, got {source}"
        assert dest['folder_name'] == "Block", f"Expected Block, got {dest['folder_name']}"
    else:
        print("✗ FAIL: No match found")
        return False

    return True


def test_keyword_pattern():
    """Test that keyword patterns are matched correctly."""
    print("\n" + "="*60)
    print("TEST 2: Keyword Pattern Matching")
    print("="*60)

    patterns = load_learned_patterns()

    # Test with meeting that should match keyword pattern
    meeting_title = "Production Meeting"
    meeting_content = """
    We need to review the production brief for the BevMo holiday campaign.
    Timeline is tight so we need to move quickly.
    """

    result = apply_learned_patterns(meeting_title, meeting_content, patterns)

    if result:
        dest, confidence, source = result
        print(f"✓ PASS: Matched via {source}")
        print(f"  Destination: {dest['folder_name']} → {dest['list_name']}")
        print(f"  Confidence: {confidence:.0%}")
        assert source == "keyword_pattern", f"Expected keyword_pattern, got {source}"
        assert dest['folder_name'] == "BevMo", f"Expected BevMo, got {dest['folder_name']}"
    else:
        print("✗ FAIL: No match found")
        return False

    return True


def test_project_alias():
    """Test that project aliases are resolved correctly."""
    print("\n" + "="*60)
    print("TEST 3: Project Alias Matching")
    print("="*60)

    patterns = load_learned_patterns()

    # Test with meeting that mentions a project alias
    meeting_title = "Creative Review"
    meeting_content = """
    Let's review the latest concepts for the BitKey campaign.
    We need to finalize the messaging this week.
    """

    result = apply_learned_patterns(meeting_title, meeting_content, patterns)

    if result:
        dest, confidence, source = result
        print(f"✓ PASS: Matched via {source}")
        print(f"  Destination: {dest['folder_name']} → {dest['list_name']}")
        print(f"  Confidence: {confidence:.0%}")
        # Project alias should match
        assert dest['folder_name'] == "Block", f"Expected Block, got {dest['folder_name']}"
    else:
        print("✗ FAIL: No match found")
        return False

    return True


def test_no_match():
    """Test that meetings without patterns don't match."""
    print("\n" + "="*60)
    print("TEST 4: No Match Scenario")
    print("="*60)

    patterns = load_learned_patterns()

    # Test with meeting that should NOT match any pattern
    meeting_title = "Random Team Sync"
    meeting_content = """
    Let's discuss some general team topics.
    No specific project mentioned here.
    """

    result = apply_learned_patterns(meeting_title, meeting_content, patterns)

    if result:
        dest, confidence, source = result
        print(f"✗ FAIL: Unexpected match found via {source}")
        print(f"  Destination: {dest['folder_name']} → {dest['list_name']}")
        return False
    else:
        print("✓ PASS: No match found (as expected)")

    return True


def test_save_new_pattern():
    """Test saving a new pattern to the database."""
    print("\n" + "="*60)
    print("TEST 5: Save New Pattern")
    print("="*60)

    # Use a temporary file for testing
    test_file = 'test_patterns.json'

    # Save a new pattern
    destination = {
        'folder_name': 'Test Folder',
        'list_name': 'Test List',
        'list_id': '123456'
    }

    context = {
        'meeting_title': 'Test Meeting',
        'date': '2025-10-19',
        'context_text': 'test context',
        'notes': 'This is a test pattern'
    }

    save_learned_pattern(
        pattern_type='title_patterns',
        pattern_key='test meeting',
        destination=destination,
        context=context,
        json_file_path=test_file
    )

    # Load and verify
    from meeting_learning import load_learned_patterns
    patterns = load_learned_patterns(test_file)

    if 'test meeting' in patterns['patterns']['title_patterns']:
        saved_pattern = patterns['patterns']['title_patterns']['test meeting']
        print("✓ PASS: Pattern saved successfully")
        print(f"  Destination: {saved_pattern['destination']['folder_name']}")
        print(f"  Confidence: {saved_pattern['confidence']}")

        # Clean up test file
        import os
        os.remove(test_file)
        return True
    else:
        print("✗ FAIL: Pattern not found in database")
        return False


def test_normalize_text():
    """Test text normalization."""
    print("\n" + "="*60)
    print("TEST 6: Text Normalization")
    print("="*60)

    tests = [
        ("Chad : Drew : Rose", "chad drew rose"),
        ("BevMo!!!", "bevmo"),
        ("Mike's  Hot   Honey", "mike s hot honey"),
        ("GO-PUFF/NYE", "go puff nye")
    ]

    all_pass = True
    for input_text, expected in tests:
        result = normalize_text(input_text)
        if result == expected:
            print(f"✓ PASS: '{input_text}' → '{result}'")
        else:
            print(f"✗ FAIL: '{input_text}' → '{result}' (expected '{expected}')")
            all_pass = False

    return all_pass


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*70)
    print(" LEARNING SYSTEM TEST SUITE")
    print("="*70)

    tests = [
        ("Title Pattern Matching", test_title_pattern),
        ("Keyword Pattern Matching", test_keyword_pattern),
        ("Project Alias Matching", test_project_alias),
        ("No Match Scenario", test_no_match),
        ("Save New Pattern", test_save_new_pattern),
        ("Text Normalization", test_normalize_text)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ ERROR in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*70)
    print(" TEST RESULTS SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n{passed}/{total} tests passed ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
