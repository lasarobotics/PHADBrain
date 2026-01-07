import edu.wpi.first.networktables.*;

public class FADPublisher {

    private final NetworkTable table;

    private final DoubleArrayPublisher posePub;
    private final DoubleArrayPublisher velocityPub;
    private final DoubleArrayPublisher visionLeftPub;
    private final DoubleArrayPublisher visionRightPub;

    public FADPublisher() {
        NetworkTableInstance inst = NetworkTableInstance.getDefault();

        // RoboRIO acts as NT server automatically
        table = inst.getTable("FAD");

        posePub = table.getDoubleArrayTopic("pose").publish();
        velocityPub = table.getDoubleArrayTopic("velocity").publish();
        visionLeftPub = table.getDoubleArrayTopic("vision/left").publish();
        visionRightPub = table.getDoubleArrayTopic("vision/right").publish();
    }

    public void publish(
            double x, double y, double heading,
            double vx, double vy, double omega,
            double leftConfidence, double rightConfidence
    ) {
        posePub.set(new double[]{x, y, heading});
        velocityPub.set(new double[]{vx, vy, omega});
        visionLeftPub.set(new double[]{leftConfidence});
        visionRightPub.set(new double[]{rightConfidence});
    }
}
