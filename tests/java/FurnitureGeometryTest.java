import com.realistichomedecor.util.FurnitureGeometry;
import com.realistichomedecor.util.FurnitureGeometry.Box;
import com.realistichomedecor.util.FurnitureGeometry.GridOffset;
import com.realistichomedecor.util.FurnitureGeometry.Rotation;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** Standalone regression harness; throws on failure without relying on -ea. */
public final class FurnitureGeometryTest {
    private static int assertions;

    private static void require(boolean condition, String message) {
        assertions++;
        if (!condition) throw new AssertionError(message);
    }

    private static void rejects(Class<? extends Throwable> type, Runnable operation, String message) {
        assertions++;
        try {
            operation.run();
        } catch (Throwable failure) {
            if (type.isInstance(failure)) return;
            throw new AssertionError(message + ": unexpected " + failure, failure);
        }
        throw new AssertionError(message + ": accepted invalid input");
    }

    private static double volume(Box box) {
        return (box.maxX() - box.minX()) * (box.maxY() - box.minY()) * (box.maxZ() - box.minZ());
    }

    public static void main(String[] args) {
        Box source = new Box(1, 2, 3, 4, 5, 6);
        require(FurnitureGeometry.rotate(source, Rotation.NORTH).equals(source), "north identity");
        require(FurnitureGeometry.rotate(source, Rotation.EAST).equals(new Box(10, 2, 1, 13, 5, 4)), "east model rotation");
        require(FurnitureGeometry.rotate(source, Rotation.SOUTH).equals(new Box(12, 2, 10, 15, 5, 13)), "south model rotation");
        require(FurnitureGeometry.rotate(source, Rotation.WEST).equals(new Box(3, 2, 12, 6, 5, 15)), "west model rotation");
        GridOffset offset = new GridOffset(2, 3, 5);
        require(FurnitureGeometry.rotate(offset, Rotation.EAST).equals(new GridOffset(-5, 3, 2)), "east cell rotation");
        require(FurnitureGeometry.rotate(offset, Rotation.SOUTH).equals(new GridOffset(-2, 3, -5)), "south cell rotation");
        require(FurnitureGeometry.rotate(offset, Rotation.WEST).equals(new GridOffset(5, 3, -2)), "west cell rotation");
        Random random = new Random(417813);
        for (int i = 0; i < 100; i++) {
            double x = random.nextInt(15), y = random.nextInt(15), z = random.nextInt(15);
            Box box = new Box(x, y, z, x + 1 + random.nextInt((int) (16 - x)),
                    y + 1 + random.nextInt((int) (16 - y)), z + 1 + random.nextInt((int) (16 - z)));
            Box rotated = box;
            for (int turn = 0; turn < 4; turn++) rotated = FurnitureGeometry.rotate(rotated, Rotation.EAST);
            require(rotated.equals(box), "four turns preserve box " + i);
            for (Rotation rotation : Rotation.values()) {
                Box result = FurnitureGeometry.rotate(box, rotation);
                require(volume(result) == volume(box), "rotation preserves collision volume " + i);
                require(result.minY() == box.minY() && result.maxY() == box.maxY(), "rotation preserves height " + i);
            }
            GridOffset cell = new GridOffset(random.nextInt(31) - 15, random.nextInt(16), random.nextInt(31) - 15);
            GridOffset cellTurned = cell;
            for (int turn = 0; turn < 4; turn++) cellTurned = FurnitureGeometry.rotate(cellTurned, Rotation.EAST);
            require(cellTurned.equals(cell), "four turns preserve cell " + i);
        }
        rejects(IllegalArgumentException.class, () -> new Box(0, 0, 0, 0, 1, 1), "zero volume");
        rejects(IllegalArgumentException.class, () -> new Box(2, 0, 0, 1, 1, 1), "inverted box");
        rejects(IllegalArgumentException.class, () -> new Box(-1, 0, 0, 1, 1, 1), "negative cell coordinate");
        rejects(IllegalArgumentException.class, () -> new Box(0, 0, 0, 17, 1, 1), "overflowing cell coordinate");
        rejects(IllegalArgumentException.class, () -> new Box(Double.NaN, 0, 0, 1, 1, 1), "NaN coordinate");
        rejects(IllegalArgumentException.class, () -> new Box(0, 0, 0, Double.POSITIVE_INFINITY, 1, 1), "infinite coordinate");
        rejects(ArithmeticException.class, () -> FurnitureGeometry.rotate(new GridOffset(0, 0, Integer.MIN_VALUE), Rotation.EAST), "integer overflow");
        rejects(NullPointerException.class, () -> FurnitureGeometry.rotate(source, null), "missing rotation");
        ArrayList<Box> original = new ArrayList<>(List.of(source));
        List<Box> transformed = FurnitureGeometry.rotate(original, Rotation.EAST);
        require(original.equals(List.of(source)), "rotation preserves input list");
        require(transformed.equals(List.of(new Box(10, 2, 1, 13, 5, 4))), "list rotation matches scalar");
        rejects(UnsupportedOperationException.class, () -> transformed.add(source), "result list is immutable");
        System.out.println("FurnitureGeometry: " + assertions + " assertions passed");
    }
}
