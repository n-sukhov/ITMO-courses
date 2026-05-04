$fn = 96;


base_x = 90;
base_y = 160;
base_z = 10;

trap_x = 90;
trap_y_bottom = 130;
trap_y_top = 60;
trap_z = 40;
trap_y_shift = 0;

top_x = 90;
top_y = 60;
top_z = 40;

top_y_shift = trap_y_shift;

hole_z_d = 50;
hole_z_x = 0;
hole_z_y = 0;

hole_y_d = 30;
hole_y_x = 0;

hole_y_z = base_z + trap_z + top_z / 2;

slot_x = 50;
slot_y = 162;
slot_z = 25;

slot_y_start = -base_y / 2 - 1;

eps = 0.2;


module base_block() {
    translate([-base_x / 2, -base_y / 2, 0])
        cube([base_x, base_y, base_z]);
}


module top_block() {
    translate([
        -top_x / 2,
        top_y_shift - top_y / 2,
        base_z + trap_z
    ])
        cube([top_x, top_y, top_z]);
}


module trapezoid_body() {
    x0 = -trap_x / 2;
    x1 =  trap_x / 2;

    z0 = base_z;
    z1 = base_z + trap_z;

    yb0 = -trap_y_bottom / 2;
    yb1 =  trap_y_bottom / 2;

    yt0 = trap_y_shift - trap_y_top / 2;
    yt1 = trap_y_shift + trap_y_top / 2;

    polyhedron(
        points = [
            [x0, yb0, z0],
            [x1, yb0, z0],
            [x1, yb1, z0],
            [x0, yb1, z0],

            [x0, yt0, z1],
            [x1, yt0, z1],
            [x1, yt1, z1],
            [x0, yt1, z1]
        ],
        faces = [
            [0, 1, 2, 3],
            [4, 7, 6, 5],

            [0, 4, 5, 1],
            [1, 5, 6, 2],
            [2, 6, 7, 3],
            [3, 7, 4, 0]
        ]
    );
}


module vertical_z_hole() {
    translate([hole_z_x, hole_z_y, base_z - eps])
        cylinder(
            h = trap_z + top_z + 2 * eps,
            d = hole_z_d
        );
}


module horizontal_y_hole() {
    translate([hole_y_x, top_y_shift, hole_y_z])
        rotate([90, 0, 0])
            cylinder(
                h = top_y + 2 * eps,
                d = hole_y_d,
                center = true
            );
}


module rectangular_slot() {
    translate([
        -slot_x / 2,
        slot_y_start,
        -eps
    ])
        cube([
            slot_x,
            slot_y,
            slot_z + eps
        ]);
}


difference() {
    union() {
        base_block();
        trapezoid_body();
        top_block();
    }

    vertical_z_hole();
    horizontal_y_hole();
    rectangular_slot();
}