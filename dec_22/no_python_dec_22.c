#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DA_NEW() {.elements = NULL, .length = 0, .capacity = 0}

#define DA_PUSH(da, element) do { \
    if ((da).length >= (da).capacity) { \
        (da).capacity = ((da).capacity == 0) ? 1 : (2 * (da).capacity); \
        (da).elements = realloc( \
            (da).elements, (da).capacity * sizeof(*(da).elements) \
        ); \
        if ((da).elements == NULL) { \
            fprintf(stderr, "ran out of memory for dynamic array\n"); \
            exit(EXIT_FAILURE); \
        } \
    } \
    (da).elements[(da).length] = (element); \
    (da).length += 1; \
} while (0)

#define DA_DELETE(da) do { \
    if ((da).elements != NULL) { \
        free((da).elements); \
    } \
    (da).elements = NULL; \
    (da).length = 0; \
    (da).capacity = 0; \
} while (0)

typedef enum : uint8_t {OFF = 0, ON = 1} OnOff;

typedef struct {
    int64_t x1, x2;
    int64_t y1, y2;
    int64_t z1, z2;
} Cuboid;

typedef struct {
    Cuboid * elements;
    size_t length;
    size_t capacity;
} Cuboids;

#define CHAINED_LE_LE(a, b, c) ( ((a) <= (b)) && ((b) <= (c)) )

bool cuboid_contains(const Cuboid * outer, const Cuboid * inner) {
    return (
        CHAINED_LE_LE(outer->x1, inner->x1, outer->x2)
        && CHAINED_LE_LE(outer->x1, inner->x2, outer->x2)
        && CHAINED_LE_LE(outer->y1, inner->y1, outer->y2)
        && CHAINED_LE_LE(outer->y1, inner->y2, outer->y2)
        && CHAINED_LE_LE(outer->z1, inner->z1, outer->z2)
        && CHAINED_LE_LE(outer->z1, inner->z2, outer->z2)
    );
}

#define CHAINED_LE_LT_LE(a, b, c, d) ( \
    ((a) <= (b)) && ((b) < (c)) && ((c) <= (d)) \
)

bool cuboid_overlaps_with(const Cuboid * cuboid, const Cuboid * other) {
    return !(
        CHAINED_LE_LT_LE(other->x1, other->x2, cuboid->x1, cuboid->x2)
        || CHAINED_LE_LT_LE(cuboid->x1, cuboid->x2, other->x1, other->x2)
        || CHAINED_LE_LT_LE(other->y1, other->y2, cuboid->y1, cuboid->y2)
        || CHAINED_LE_LT_LE(cuboid->y1, cuboid->y2, other->y1, other->y2)
        || CHAINED_LE_LT_LE(other->z1, other->z2, cuboid->z1, cuboid->z2)
        || CHAINED_LE_LT_LE(cuboid->z1, cuboid->z2, other->z1, other->z2)
    );
}

#define NONNEGATIVE_WIDTH(lower, upper) ( \
    ((lower) <= (upper)) ? ((upper) - (lower) + 1) : 0 \
)

int64_t cuboid_size(const Cuboid * cuboid) {
    return (
        NONNEGATIVE_WIDTH(cuboid->x1, cuboid->x2)
        * NONNEGATIVE_WIDTH(cuboid->y1, cuboid->y2)
        * NONNEGATIVE_WIDTH(cuboid->z1, cuboid->z2)
    );
}

#define MIN(a, b) ( ((a) <= (b)) ? (a) : (b) )

#define MAX(a, b) ( ((a) >= (b)) ? (a) : (b) )

Cuboid cuboid_intersection(const Cuboid * cuboid, const Cuboid * other) {
    if (cuboid_size(cuboid) == 0 || cuboid_size(other) == 0) {
        fprintf(stderr, "intersection with a cuboid of size zero\n");
        exit(EXIT_FAILURE);
    }

    int64_t x1 = MAX(cuboid->x1, other->x1);
    int64_t x2 = MIN(cuboid->x2, other->x2);
    int64_t y1 = MAX(cuboid->y1, other->y1);
    int64_t y2 = MIN(cuboid->y2, other->y2);
    int64_t z1 = MAX(cuboid->z1, other->z1);
    int64_t z2 = MIN(cuboid->z2, other->z2);

    return (Cuboid) {
        .x1 = x1, .x2 = x2, .y1 = y1, .y2 = y2, .z1 = z1, .z2 = z2
    };
}

bool cuboid_equal(const Cuboid * cuboid, const Cuboid * other) {
    return (
        cuboid->x1 == other->x1 && cuboid->x2 == other->x2
        && cuboid->y1 == other->y1 && cuboid->y2 == other->y2
        && cuboid->z1 == other->z1 && cuboid->z2 == other->z2
    );
}

void cuboid_shatter_around(
    Cuboids * shattered_pieces, const Cuboid * cuboid, const Cuboid * other
) {
    if (!cuboid_contains(cuboid, other)) {
        fprintf(stderr, "cuboid must be contained to shatter around\n");
        exit(EXIT_FAILURE);
    }

    int64_t x_spans[3][2] = {
        {cuboid->x1, other->x1 - 1},
        {other->x1, other->x2},
        {other->x2 + 1, cuboid->x2},
    };
    int64_t y_spans[3][2] = {
        {cuboid->y1, other->y1 - 1},
        {other->y1, other->y2},
        {other->y2 + 1, cuboid->y2},
    };
    int64_t z_spans[3][2] = {
        {cuboid->z1, other->z1 - 1},
        {other->z1, other->z2},
        {other->z2 + 1, cuboid->z2},
    };

    for (size_t i = 0; i < 3; i++) {
        for (size_t j = 0; j < 3; j++) {
            for (size_t k = 0; k < 3; k++) {
                Cuboid new_piece = {
                    .x1 = x_spans[i][0], .x2 = x_spans[i][1],
                    .y1 = y_spans[j][0], .y2 = y_spans[j][1],
                    .z1 = z_spans[k][0], .z2 = z_spans[k][1]
                };
                if (
                    cuboid_size(&new_piece) != 0
                    && !cuboid_equal(&new_piece, other)
                ) {
                    DA_PUSH(*shattered_pieces, new_piece);
                }
            }
        }
    }
}

typedef struct {
    OnOff on_off;
    Cuboid cuboid;
} RebootStep;

typedef struct {
    RebootStep * elements ;
    size_t length;
    size_t capacity;
} RebootSteps;

void read_reboot_steps(RebootSteps * reboot_steps, const char * file) {
    FILE * fp = fopen(file, "r");

    while (true) {
        char on_off_string[5];
        Cuboid cuboid;
        int values_assigned = fscanf(
            fp, "%s x=%ld..%ld,y=%ld..%ld,z=%ld..%ld",
            on_off_string,
            &cuboid.x1, &cuboid.x2,
            &cuboid.y1, &cuboid.y2,
            &cuboid.z1, &cuboid.z2
        );
        if (values_assigned != 7) {
            break;
        }
        OnOff on_off = (strcmp("on", on_off_string) == 0) ? ON : OFF;
        RebootStep step = {.on_off = on_off, .cuboid = cuboid};
        DA_PUSH(*reboot_steps, step);
    }

    fclose(fp);
}

const Cuboid INITIALIZATION_REGION = {
    .x1 = -50, .x2 = 50, .y1 = -50, .y2 = 50, .z1 = -50, .z2 = 50
};

void filter_initialization_steps(
    RebootSteps * initialization_steps, const RebootSteps * reboot_steps
) {
    for (size_t i = 0; i < reboot_steps->length; i++) {
        const RebootStep * step = &reboot_steps->elements[i];
        if (cuboid_contains(&INITIALIZATION_REGION, &step->cuboid)) {
            DA_PUSH(*initialization_steps, *step);
        }
    }
}

void delete_cuboid_region(
    Cuboids * new_active_cuboids,
    const Cuboids * active_cuboids,
    const Cuboid * delete_region
) {
    for (size_t i = 0; i < active_cuboids->length; i++) {
        const Cuboid * cuboid = &active_cuboids->elements[i];

        if (!cuboid_overlaps_with(cuboid, delete_region)) {
            DA_PUSH(*new_active_cuboids, *cuboid);
            continue;
        }

        Cuboid intersection = cuboid_intersection(cuboid, delete_region);
        Cuboids shattered_cuboid_pieces = DA_NEW();
        cuboid_shatter_around(&shattered_cuboid_pieces, cuboid, &intersection);
        for (size_t j = 0; j < shattered_cuboid_pieces.length; j++) {
            DA_PUSH(*new_active_cuboids, shattered_cuboid_pieces.elements[j]);
        }
        DA_DELETE(shattered_cuboid_pieces);
    }
}

int64_t number_of_cubes_turned_on(const RebootSteps * reboot_steps) {
    Cuboids active_cuboids = DA_NEW();
    for (size_t i = 0; i < reboot_steps->length; i++) {
        const RebootStep * step = &reboot_steps->elements[i];

        Cuboids new_active_cuboids = DA_NEW();
        delete_cuboid_region(
            &new_active_cuboids, &active_cuboids, &step->cuboid
        );
        DA_DELETE(active_cuboids);
        active_cuboids = new_active_cuboids;

        if (step->on_off == ON) {
            DA_PUSH(active_cuboids, step->cuboid);
        }
    }

    int64_t result = 0;
    for (size_t i = 0; i < active_cuboids.length; i++) {
        result += cuboid_size(&active_cuboids.elements[i]);
    }
    return result;
}

void part_1(const char * file) {
    RebootSteps reboot_steps = DA_NEW();
    read_reboot_steps(&reboot_steps, file);

    RebootSteps initialization_steps = DA_NEW();
    filter_initialization_steps(&initialization_steps, &reboot_steps);

    int64_t cube_count = number_of_cubes_turned_on(&initialization_steps);
    printf("part 1: %ld\n", cube_count);

    DA_DELETE(initialization_steps);
    DA_DELETE(reboot_steps);
}

void part_2(const char * file) {
    RebootSteps reboot_steps = DA_NEW();
    read_reboot_steps(&reboot_steps, file);

    int64_t full_cube_count = number_of_cubes_turned_on(&reboot_steps);
    printf("part 2: %ld\n", full_cube_count);
}

int main(int argc, char ** argv) {
    if (argc != 2) {
        fprintf(stderr, "one argument is required: input file path\n");
        return EXIT_FAILURE;
    }

    part_1(argv[1]);
    part_2(argv[1]);

    return EXIT_SUCCESS;
}
