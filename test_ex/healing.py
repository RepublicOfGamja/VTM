import sys
import os
import time
import logging
from typing import Union

# Module import via relative path settings
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
os.chdir(current_script_dir)

# Import VectorWave core modules and Healer
from vectorwave import vectorize, initialize_database, generate_and_register_metadata
from vectorwave.utils.healer import VectorWaveHealer
# tracer is used indirectly via vectorize

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Define Custom Error for testing
class TestBugError(Exception):
    def __init__(self, message, error_code="TEST_BUG"):
        super().__init__(message)
        self.error_code = error_code


def run_e2e_healer_test():
    client = None
    func_name = "buggy_adder"
    lookback_minutes = 10

    print("=" * 60)
    print("🚀 Starting VectorWave Healer E2E Test")
    print("=" * 60)

    try:
        # 1. Initialize and connect to database
        print("1. Connecting and initializing DB...")
        client = initialize_database()
        if not client:
            raise ConnectionError("Database initialization failed. Check Weaviate/DB settings.")

        # 2. Define test function (includes intentional bug)
        @vectorize(
            search_description="A function that adds two numbers. It contains an intentional type error bug.",
            team="healer-e2e-test",
            auto=True,
            priority=1
        )
        def buggy_adder(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
            print(f"  [FUNC] {func_name} called: {a}, {b}")
            # [MODIFIED] If b is 0, run normally (for success log), otherwise raise error (for failure log)
            if b == 0:
                return a + 0 # Execute normal logic for success log
            else:
                # Intentional bug: Attempt to add string "error" to input a, triggering TypeError
                return a + "error"

        # 3. Register function metadata (Store source code in DB)
        print("\n2. Registering bug function metadata and source code...")
        # Previous: generate_and_register_metadata(function_name_filter=func_name)
        # Modified: Called without arguments
        generate_and_register_metadata()

        # 4. Record successful execution (Creating SUCCESS log for Healer reference)
        print("\n3. Recording successful execution (Creating SUCCESS log for Healer reference)...")
        try:
            # Call with b=0 to induce successful termination
            buggy_adder(a=100, b=0)
            print("  -> Successful execution log recorded.")
        except Exception as e:
            # Print if success logic failed unexpectedly
            print(f"  -> Warning: Unexpected error during success execution recording: {e.__class__.__name__}: {e}")

        # 5. Record failed execution (Creating recent ERROR log for Healer to find)
        print("4. Recording failed execution (Creating recent ERROR log for Healer to find)...")
        try:
            # Call with b=1 (non-zero) to intentionally trigger TypeError
            buggy_adder(a=100, b=1)
        except Exception as e:
            # Traceback records the TypeError
            print(f"  -> Intentional error occurred and recorded: {e.__class__.__name__}: {e}")

        # Allow time for logs to be written to DB (assuming async processing)
        print("  -> Waiting 5 seconds for log DB recording...")
        time.sleep(5)

        # 6. Execute VectorWaveHealer
        print(f"\n5. Executing VectorWaveHealer: Starting diagnosis for '{func_name}'")

        healer = VectorWaveHealer(model="gpt-4-turbo-2024-04-09")
        suggested_fix = healer.diagnose_and_heal(
            function_name=func_name,
            lookback_minutes=lookback_minutes
        )

        print("\n" + "=" * 60)
        print("✅ Healer Diagnosis Result (LLM suggested fix):")
        print("=" * 60)
        print(suggested_fix)
        print("=" * 60)

        # 7. Verify Result
        if "a + b" in suggested_fix and "b == 0" not in suggested_fix:
            print("\n🎉 Test Success: LLM correctly diagnosed the bug and suggested a fix.")
        else:
            print("\n⚠️ Test Warning: LLM suggested unexpected code or the fix might be incomplete.")

    except ConnectionError as ce:
        print(f"\n❌ [Connection Error] Cannot execute test: {ce}")
        print("  -> Please check Weaviate server and OPENAI_API_KEY settings.")
    except Exception as e:
        logger.error(f"\n❌ [Fatal Error] E2E Test Failed: {e}", exc_info=True)

    finally:
        print("\n" + "=" * 60)
        print("✨ VectorWave Healer E2E Test Completed.")
        print("=" * 60)


if __name__ == '__main__':
    run_e2e_healer_test()