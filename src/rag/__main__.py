from loguru import logger


def main():
    """Entry point for the application."""
    from rag.cli import cli

    try:
        cli()
    except KeyboardInterrupt:
        logger.info("Interrupt signal received. Exiting...")
        raise SystemExit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise e
    else:
        logger.info("Finished program execution.")
        raise SystemExit(0)


if __name__ == "__main__":
    app = main()
