from trajectory_logger import TrajectoryLogger


def test_trajectory_logger_records_events():
    logger = TrajectoryLogger()

    logger.log(
        attempt=1,
        query="leave after joining",
        score=0.57,
        best_score=0.57,
        score_delta=0.0,
        chunk_overlap=0.0,
        decision="INSUFFICIENT"
    )

    logger.log(
        attempt=2,
        query="leave eligibility during probation",
        score=0.78,
        best_score=0.78,
        score_delta=0.21,
        chunk_overlap=0.33,
        decision="SUFFICIENT"
    )

    records = logger.get_records()

    assert len(records) == 2
    assert records[0]["attempt"] == 1
    assert records[1]["attempt"] == 2
    assert records[1]["decision"] == "SUFFICIENT"